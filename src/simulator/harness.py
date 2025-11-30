from typing import Dict, List, Any, Set

from src.network.simulator import NetworkSimulator, NetworkConfig


class VoteTrackingNode:
    """
    Node mô phỏng gửi/nhận vote qua NetworkSimulator.
    - Lưu inbound messages.
    - Đếm số PRECOMMIT nhận được (unique validator) để kiểm tra finalized.
    """

    def __init__(self, node_id: str, peers: List[str], network: NetworkSimulator,
                 height: int, block_hash: str, consensus_log: List[Dict[str, Any]]):
        self.node_id = node_id
        self.peers = peers
        self.network = network
        self.height = height
        self.block_hash = block_hash
        self.inbound: List[Dict[str, Any]] = []
        self.precommit_from: Set[str] = set()
        self.consensus_log = consensus_log

        self.network.register_node(node_id, self.on_message)

    def _log(self, event: str, details: Dict[str, Any]):
        self.consensus_log.append({
            "time_ms": self.network.now_ms,
            "event": event,
            "node": self.node_id,
            **details,
        })

    def on_message(self, msg: Dict[str, Any]):
        payload = msg.get("payload", {})
        self.inbound.append(msg)

        if payload.get("type") == "VOTE" and payload.get("phase") == "PRECOMMIT":
            voter = payload.get("from")
            if voter:
                self.precommit_from.add(voter)
        # Log nhận proposal/vote
        if payload.get("type") == "PROPOSAL":
            self._log("CONSENSUS_PROPOSAL_RECV", {
                "from": msg.get("from"),
                "height": payload.get("height"),
                "block_hash": payload.get("block_hash"),
            })
        elif payload.get("type") == "VOTE":
            self._log(f"CONSENSUS_{payload.get('phase')}_RECV", {
                "from": payload.get("from"),
                "height": payload.get("height"),
                "block_hash": payload.get("block_hash"),
            })

    def broadcast_proposal(self):
        payload = {
            "type": "PROPOSAL",
            "block_hash": self.block_hash,
            "height": self.height,
        }
        self._log("CONSENSUS_PROPOSAL_SEND", {
            "height": self.height,
            "block_hash": self.block_hash,
        })
        for peer in self.peers + [self.node_id]:
            self.network.send_header(
                sender=self.node_id,
                receiver=peer,
                header_id=f"proposal-{self.height}-{self.node_id}-{peer}",
                height=self.height,
                payload=payload,
            )

    def broadcast_vote(self, phase: str):
        payload = {
            "type": "VOTE",
            "phase": phase,
            "height": self.height,
            "block_hash": self.block_hash,
            "from": self.node_id,
        }
        self._log(f"CONSENSUS_{phase}_SEND", {
            "height": self.height,
            "block_hash": self.block_hash,
        })
        for peer in self.peers + [self.node_id]:
            self.network.send_header(
                sender=self.node_id,
                receiver=peer,
                header_id=f"vote-{phase}-{self.node_id}-{peer}",
                height=self.height,
                payload=payload,
            )


def run_consensus_smoke_simple(
    num_nodes: int = 4,
    height: int = 1,
    block_hash: str = "hash_cua_block_so_1",
    seed: int = 123,
) -> Dict[str, Any]:
    """
    Smoke test consensus flow qua NetworkSimulator (không dùng engine phức tạp):
    - Proposer broadcast proposal.
    - Tất cả node broadcast PREVOTE.
    - Sau đó tất cả node broadcast PRECOMMIT.
    - Finalized nếu nhận >= 2/3+1 precommit.
    """
    cfg = NetworkConfig(
        base_delay_ms=5,
        jitter_ms=0,
        drop_rate=0.0,
        duplicate_rate=0.0,
        max_inflight_per_sender=16,
        max_inflight_per_link=16,
        max_bytes_inflight_per_link=10_000,
        link_bandwidth_bytes_per_ms=1000,
    )
    net = NetworkSimulator(seed=seed, config=cfg)

    consensus_log: List[Dict[str, Any]] = []
    node_ids = [str(i) for i in range(num_nodes)]
    nodes: Dict[str, VoteTrackingNode] = {}
    for nid in node_ids:
        peers = [p for p in node_ids if p != nid]
        nodes[nid] = VoteTrackingNode(nid, peers, net, height=height, block_hash=block_hash,
                                      consensus_log=consensus_log)

    # Topology full mesh
    edges = [(a, b) for a in node_ids for b in node_ids if a != b]
    net.load_topology(edges)

    proposer = nodes[node_ids[0]]
    proposer.broadcast_proposal()
    net.run_until_idle()

    # All nodes broadcast PREVOTE
    for n in nodes.values():
        n.broadcast_vote("PREVOTE")
    net.run_until_idle()

    # All nodes broadcast PRECOMMIT
    for n in nodes.values():
        n.broadcast_vote("PRECOMMIT")
    net.run_until_idle()

    threshold = (num_nodes * 2) // 3 + 1
    finalized = {
        nid: (len(n.precommit_from) >= threshold)
        for nid, n in nodes.items()
    }
    finalized_count = sum(1 for v in finalized.values() if v)
    for nid, ok in finalized.items():
        consensus_log.append({
            "time_ms": net.now_ms,
            "event": "CONSENSUS_FINALIZE" if ok else "CONSENSUS_NOT_FINAL",
            "node": nid,
            "height": height,
            "block_hash": block_hash,
        })

    return {
        "finalized": finalized,
        "finalized_count": finalized_count,
        "network_logs": net.logs(),
        "consensus_logs": consensus_log,
    }

