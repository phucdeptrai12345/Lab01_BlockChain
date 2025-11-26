import heapq
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple, Any


# Types for clarity
MessageHandler = Callable[[Dict[str, Any]], None]


@dataclass
class NetworkConfig:
    """
    Basic knobs for the unreliable network.
    """
    base_delay_ms: int = 50  # minimum delay
    jitter_ms: int = 100     # added randomness
    drop_rate: float = 0.0   # probability [0,1]
    duplicate_rate: float = 0.0  # probability [0,1] to duplicate a delivery
    max_inflight_per_sender: int = 64  # simple rate limit
    max_inflight_per_link: int = 32  # simple per-link limit
    max_bytes_inflight_per_link: int = 1_000_000  # soft bandwidth cap
    auto_block_inflight_threshold: int = 128  # auto block if inflight messages exceed
    auto_block_duration_ms: int = 5000        # how long to auto block
    link_bandwidth_bytes_per_ms: int = 50      # serialize sends on a link (throughput)
    rate_window_ms: int = 1000                 # for rate-based auto blocking
    max_msgs_per_link_per_window: Optional[int] = None  # if set, block when exceeded


@dataclass(order=True)
class ScheduledMessage:
    deliver_at: float
    msg_id: int = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)


class NetworkSimulator:
    """
    Simulates an unreliable network:
    - Messages delayed, duplicated, dropped.
    - Headers must arrive before bodies (tracked by header_id).
    - Per-sender inflight cap; extra messages are dropped.
    - All events logged deterministically (seeded RNG).
    """

    def __init__(self, seed: int = 0, config: Optional[NetworkConfig] = None):
        self.config = config or NetworkConfig()
        self.rng = random.Random(seed)
        self.handlers: Dict[str, MessageHandler] = {}
        self.now_ms = 0.0
        self._queue: List[ScheduledMessage] = []
        self._next_msg_id = 1
        self._logs: List[Dict[str, Any]] = []
        self._inflight_count: Dict[str, int] = {}
        self._inflight_link: Dict[Tuple[str, str], int] = {}
        self._inflight_bytes_link: Dict[Tuple[str, str], int] = {}
        # Track which receivers have seen headers to allow bodies
        self._seen_headers: Dict[Tuple[str, str], bool] = {}
        # Optional topology
        self._allowed_edges: Optional[Set[Tuple[str, str]]] = None
        self._blocked_links: Set[Tuple[str, str]] = set()
        self._auto_blocked_until: Dict[Tuple[str, str], float] = {}
        # Backpressure queue per link
        self._pending_link: Dict[Tuple[str, str], List[Tuple[Dict[str, Any], int]]] = {}
        # Track serialization/throughput per link
        self._link_next_available_time: Dict[Tuple[str, str], float] = {}
        # Optional per-link parameters (delay/jitter/bandwidth/drop)
        self._link_profile: Dict[Tuple[str, str], Dict[str, Any]] = {}
        # Rate tracking per link for auto block based on bursts
        self._link_send_times: Dict[Tuple[str, str], deque] = {}

    # Public API -----------------------------------------------------
    def register_node(self, node_id: str, handler: MessageHandler) -> None:
        self.handlers[node_id] = handler
        self._inflight_count.setdefault(node_id, 0)
        # Per-link counters created lazily

    def load_topology(self, edges: List[Tuple[str, str]]) -> None:
        """
        Restrict network to directed edges (sender, receiver).
        If not set, network is fully connected.
        """
        self._allowed_edges = set(edges)

    def load_topology_from_file(self, path: str) -> None:
        """
        Load topology from a simple CSV-like file:
        each non-empty, non-comment line is "sender,receiver".
        """
        edges: List[Tuple[str, str]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) != 2:
                    continue
                edges.append((parts[0], parts[1]))
        self.load_topology(edges)

    def load_link_profile_from_file(self, path: str) -> None:
        """
        CSV-like file with fields:
        sender,receiver,base_delay_ms,jitter_ms,bandwidth_bytes_per_ms,drop_rate
        Missing trailing fields fall back to defaults.
        """
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 2:
                    continue
                sender, receiver = parts[0], parts[1]
                profile: Dict[str, Any] = {}
                if len(parts) > 2 and parts[2]:
                    profile["base_delay_ms"] = int(parts[2])
                if len(parts) > 3 and parts[3]:
                    profile["jitter_ms"] = int(parts[3])
                if len(parts) > 4 and parts[4]:
                    profile["bandwidth_bytes_per_ms"] = int(parts[4])
                if len(parts) > 5 and parts[5]:
                    profile["drop_rate"] = float(parts[5])
                self._link_profile[(sender, receiver)] = profile

    def block_link(self, sender: str, receiver: str) -> None:
        self._blocked_links.add((sender, receiver))
        self._log_event("block_link", sender, receiver, None, {})

    def unblock_link(self, sender: str, receiver: str) -> None:
        self._blocked_links.discard((sender, receiver))
        self._log_event("unblock_link", sender, receiver, None, {})

    def send_header(self, sender: str, receiver: str, header_id: str,
                    height: int, payload: Dict[str, Any]) -> None:
        envelope = {
            "type": "HEADER",
            "header_id": header_id,
            "height": height,
            "from": sender,
            "to": receiver,
            "body_allowed": False,
            "payload": payload,
        }
        self._enqueue(sender, receiver, envelope)

    def send_body(self, sender: str, receiver: str, header_id: str,
                  height: int, payload: Dict[str, Any]) -> None:
        key = (receiver, header_id)
        if not self._seen_headers.get(key, False):
            self._log_event("body_rejected_missing_header", sender, receiver, height, {
                "header_id": header_id
            })
            return

        envelope = {
            "type": "BODY",
            "header_id": header_id,
            "height": height,
            "from": sender,
            "to": receiver,
            "payload": payload,
        }
        self._enqueue(sender, receiver, envelope)

    def tick(self) -> int:
        """
        Deliver all messages whose delivery time <= now.
        Returns number of delivered messages.
        """
        delivered = 0
        while self._queue and self._queue[0].deliver_at <= self.now_ms:
            scheduled = heapq.heappop(self._queue)
            msg = scheduled.payload
            sender = msg["from"]
            receiver = msg["to"]
            size_bytes = self._estimate_size(msg)
            self._inflight_count[sender] = max(self._inflight_count.get(sender, 0) - 1, 0)
            link = (sender, receiver)
            self._inflight_link[link] = max(self._inflight_link.get(link, 0) - 1, 0)
            self._inflight_bytes_link[link] = max(self._inflight_bytes_link.get(link, 0) - size_bytes, 0)

            if msg["type"] == "HEADER":
                self._seen_headers[(receiver, msg["header_id"])] = True

            self._deliver(receiver, msg)
            # After freeing capacity, try draining queued messages on this link
            self._drain_pending_link(link)
            delivered += 1
        return delivered

    def advance_time(self, delta_ms: int) -> int:
        """
        Move virtual clock forward and deliver due messages.
        """
        self.now_ms += delta_ms
        return self.tick()

    def run_until_idle(self) -> int:
        """
        Jump time to deliver all pending messages.
        """
        delivered = 0
        while self._queue:
            next_time = self._queue[0].deliver_at
            self.now_ms = next_time
            delivered += self.tick()
        return delivered

    def logs(self) -> List[Dict[str, Any]]:
        return list(self._logs)

    # Internal helpers ----------------------------------------------
    def _enqueue(self, sender: str, receiver: str, envelope: Dict[str, Any]) -> None:
        height = envelope.get("height")
        size_bytes = self._estimate_size(envelope)

        # Clear expired auto-blocks for this link if any
        self._maybe_auto_unblock(sender, receiver)

        if receiver not in self.handlers:
            self._log_event("drop_no_receiver", sender, receiver, height, envelope)
            return

        if self._allowed_edges is not None and (sender, receiver) not in self._allowed_edges:
            self._log_event("drop_disconnected", sender, receiver, height, envelope)
            return

        if self._is_blocked(sender, receiver):
            self._log_event("drop_blocked_link", sender, receiver, height, envelope)
            return

        inflight = self._inflight_count.get(sender, 0)
        if inflight >= self.config.max_inflight_per_sender:
            self._log_event("drop_rate_limit_sender", sender, receiver, height, envelope)
            return

        link = (sender, receiver)
        inflight_link = self._inflight_link.get(link, 0)
        if inflight_link >= self.config.max_inflight_per_link:
            self._log_event("drop_rate_limit_link", sender, receiver, height, envelope)
            return

        inflight_bytes = self._inflight_bytes_link.get(link, 0)
        if inflight_bytes + size_bytes > self.config.max_bytes_inflight_per_link:
            # Backpressure: queue instead of drop
            q = self._pending_link.setdefault(link, [])
            q.append((envelope, size_bytes))
            self._log_event("backpressure_queue", sender, receiver, height, {
                "queued_size": size_bytes,
                "queue_len": len(q),
                "inflight_bytes": inflight_bytes,
            })
            return

        if inflight_link + 1 >= self.config.auto_block_inflight_threshold:
            until = self.now_ms + self.config.auto_block_duration_ms
            self._auto_blocked_until[link] = until
            self._log_event("auto_block_link", sender, receiver, height, {
                "inflight": inflight_link,
                "block_until": until,
            })
            return

        if self._is_rate_overflow(link):
            until = self.now_ms + self.config.auto_block_duration_ms
            self._auto_blocked_until[link] = until
            self._log_event("auto_block_link_rate", sender, receiver, height, {
                "block_until": until,
                "window_ms": self.config.rate_window_ms,
                "max_msgs": self.config.max_msgs_per_link_per_window,
            })
            return

        drop_rate = self._get_link_drop_rate(link)
        if self.rng.random() < drop_rate:
            self._log_event("drop_random", sender, receiver, height, envelope)
            return

        # All checks passed -> schedule
        self._schedule_envelope(sender, receiver, envelope, size_bytes, inflight, inflight_link, height)

    def _schedule_envelope(self, sender: str, receiver: str, envelope: Dict[str, Any],
                           size_bytes: int, inflight_sender: int,
                           inflight_link: int, height: Optional[int]) -> None:
        # Serialize sends on link based on bandwidth
        link = (sender, receiver)
        params = self._get_link_params(link)
        start_time = max(self.now_ms, self._link_next_available_time.get(link, self.now_ms))
        tx_time = max(1, int((size_bytes + params["bandwidth"] - 1) // params["bandwidth"]))
        self._link_next_available_time[link] = start_time + tx_time

        delay = params["base_delay"] + self.rng.randint(0, params["jitter"])
        deliver_at = start_time + delay
        msg_id = self._next_msg_id
        self._next_msg_id += 1

        self._inflight_count[sender] = inflight_sender + 1
        self._inflight_link[link] = inflight_link + 1
        self._inflight_bytes_link[link] = self._inflight_bytes_link.get(link, 0) + size_bytes

        scheduled = ScheduledMessage(deliver_at=deliver_at, msg_id=msg_id, payload=envelope)
        heapq.heappush(self._queue, scheduled)
        self._log_event("delay_scheduled", sender, receiver, height, {
            "msg_id": msg_id,
            "deliver_at": deliver_at,
            "start_time_ms": start_time,
            "delay_ms": delay,
        })
        self._log_event("send", sender, receiver, height, {
            "msg_id": msg_id,
            "delay_ms": delay,
            "tx_time_ms": tx_time,
            "start_time_ms": start_time,
            "size_bytes": size_bytes,
            "envelope": envelope,
        })

        # Optional duplication counts against limits
        if self.rng.random() < self.config.duplicate_rate:
            dup_delay = delay + self.rng.randint(0, self.config.jitter_ms)
            dup = ScheduledMessage(deliver_at=self.now_ms + dup_delay,
                                   msg_id=self._next_msg_id,
                                   payload=envelope.copy())
            self._next_msg_id += 1
            heapq.heappush(self._queue, dup)
            self._inflight_count[sender] += 1
            self._inflight_link[link] = self._inflight_link.get(link, 0) + 1
            self._inflight_bytes_link[link] = self._inflight_bytes_link.get(link, 0) + size_bytes
            self._log_event("duplicate", sender, receiver, height, {
                "orig_msg_id": msg_id,
                "dup_msg_id": dup.msg_id,
                "extra_delay_ms": dup_delay - delay,
            })

    def _deliver(self, receiver: str, msg: Dict[str, Any]) -> None:
        handler = self.handlers.get(receiver)
        if not handler:
            self._log_event("drop_missing_handler", msg["from"], receiver, msg.get("height"), msg)
            return

        self._log_event("deliver", msg["from"], receiver, msg.get("height"), {
            "envelope": msg,
        })
        handler(msg)

    def _drain_pending_link(self, link: Tuple[str, str]) -> None:
        """
        Attempt to schedule queued messages for a link if capacity allows.
        """
        sender, receiver = link
        if self._is_blocked(sender, receiver):
            return

        q = self._pending_link.get(link, [])
        if not q:
            return

        inflight_sender = self._inflight_count.get(sender, 0)
        inflight_link = self._inflight_link.get(link, 0)
        inflight_bytes = self._inflight_bytes_link.get(link, 0)

        drained = 0
        while q:
            envelope, size_bytes = q[0]
            if inflight_link >= self.config.max_inflight_per_link:
                break
            if inflight_bytes + size_bytes > self.config.max_bytes_inflight_per_link:
                break
            if inflight_link + 1 >= self.config.auto_block_inflight_threshold:
                break

            q.pop(0)
            self._schedule_envelope(sender, receiver, envelope, size_bytes,
                                    inflight_sender, inflight_link, envelope.get("height"))
            inflight_sender = self._inflight_count.get(sender, inflight_sender)
            inflight_link = self._inflight_link.get(link, inflight_link)
            inflight_bytes = self._inflight_bytes_link.get(link, inflight_bytes)
            drained += 1

        if drained and not q:
            self._pending_link.pop(link, None)

    def _is_blocked(self, sender: str, receiver: str) -> bool:
        link = (sender, receiver)
        if link in self._blocked_links:
            return True
        until = self._auto_blocked_until.get(link)
        if until is None:
            return False
        if self.now_ms >= until:
            self._auto_blocked_until.pop(link, None)
            self._log_event("auto_unblock_link", sender, receiver, None, {"time_ms": self.now_ms})
            return False
        return True

    def _maybe_auto_unblock(self, sender: str, receiver: str) -> None:
        _ = self._is_blocked(sender, receiver)

    def _estimate_size(self, envelope: Dict[str, Any]) -> int:
        """
        Rough deterministic size estimate in bytes to model bandwidth.
        """
        return len(str(envelope).encode("utf-8"))

    def _get_link_params(self, link: Tuple[str, str]) -> Dict[str, int]:
        prof = self._link_profile.get(link, {})
        base_delay = prof.get("base_delay_ms", self.config.base_delay_ms)
        jitter = prof.get("jitter_ms", self.config.jitter_ms)
        bandwidth = prof.get("bandwidth_bytes_per_ms", self.config.link_bandwidth_bytes_per_ms)
        return {"base_delay": base_delay, "jitter": jitter, "bandwidth": bandwidth}

    def _get_link_drop_rate(self, link: Tuple[str, str]) -> float:
        prof = self._link_profile.get(link, {})
        return prof.get("drop_rate", self.config.drop_rate)

    def _is_rate_overflow(self, link: Tuple[str, str]) -> bool:
        if not self.config.max_msgs_per_link_per_window:
            return False
        window = self.config.rate_window_ms
        q = self._link_send_times.setdefault(link, deque())
        # Remove old timestamps
        while q and self.now_ms - q[0] > window:
            q.popleft()
        if len(q) >= self.config.max_msgs_per_link_per_window:
            return True
        q.append(self.now_ms)
        return False

    # Logging helpers
    def dump_logs(self, path: str) -> None:
        """
        Write logs to disk as JSON lines for determinism checks.
        """
        import json
        with open(path, "w", encoding="utf-8") as f:
            for entry in self._logs:
                f.write(json.dumps(entry, sort_keys=True) + "\n")

    def _log_event(self, event: str, sender: str, receiver: str,
                   height: Optional[int], details: Dict[str, Any]) -> None:
        self._logs.append({
            "time_ms": self.now_ms,
            "event": event,
            "from": sender,
            "to": receiver,
            "height": height,
            "details": details,
        })
