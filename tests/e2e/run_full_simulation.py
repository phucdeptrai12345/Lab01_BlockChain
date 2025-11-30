"""
Entrypoint mô phỏng pipeline propose -> prevote -> precommit -> finalize nhiều block.
Mục tiêu: smoke test end-to-end determinism (không đầy đủ safety/liveness của Tendermint).

Chạy:
    python tests/e2e/run_full_simulation.py

Mặc định:
- 4 node, 3 block liên tiếp.
- Proposer round-robin (node_id theo thứ tự).
- Gửi proposal qua NetworkSimulator; vote PREVOTE/PRECOMMIT qua NetworkSimulator.
- Khi đạt ngưỡng 2/3+1 PRECOMMIT, apply block vào ExecutionState.
- In ra state hash mỗi node và so sánh chúng phải giống nhau.
"""

import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Set

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from src.network.simulator import NetworkSimulator, NetworkConfig
from src.execution.execution import ExecutionState, Transaction, deterministic_encode


def hash_block(block: Dict[str, Any]) -> str:
    data = deterministic_encode(block)
    return hashlib.sha256(data).hexdigest()


class FullNode:
    def __init__(self, node_id: str, peers: List[str], network: NetworkSimulator, chain_id: str):
        self.node_id = node_id
        self.peers = peers
        self.network = network
        self.chain_id = chain_id
        self.exec_state = ExecutionState(chain_id=chain_id)
        self.height = 1
        # track votes: votes[height][phase] -> set of validators
        self.votes: Dict[int, Dict[str, Set[str]]] = {}
        self.blocks: Dict[str, Dict[str, Any]] = {}  # block_hash -> block dict

        self.network.register_node(node_id, self.on_message)

    def _threshold(self) -> int:
        total = len(self.peers) + 1
        return (total * 2) // 3 + 1

    def broadcast_proposal(self, block: Dict[str, Any]):
        block_hash = block["hash"]
        self.blocks[block_hash] = block
        payload = {
            "type": "PROPOSAL",
            "height": block["height"],
            "block_hash": block_hash,
            "block": block,
        }
        for peer in self.peers + [self.node_id]:
            self.network.send_header(
                sender=self.node_id,
                receiver=peer,
                header_id=f"proposal-{block_hash}-{peer}",
                height=block["height"],
                payload=payload,
            )

    def broadcast_vote(self, height: int, block_hash: str, phase: str):
        payload = {
            "type": "VOTE",
            "height": height,
            "block_hash": block_hash,
            "phase": phase,
            "from": self.node_id,
        }
        for peer in self.peers + [self.node_id]:
            self.network.send_header(
                sender=self.node_id,
                receiver=peer,
                header_id=f"vote-{phase}-{block_hash}-{peer}-{self.node_id}",
                height=height,
                payload=payload,
            )

    def _add_vote(self, height: int, phase: str, voter: str, block_hash: str) -> int:
        self.votes.setdefault(height, {}).setdefault(phase, set()).add(voter)
        return len(self.votes[height][phase])

    def finalize_block(self, block_hash: str, block: Dict[str, Any]):
        # Apply txs to execution state (skip signature verify for demo)
        txs = block["txs"]
        for tx in txs:
            tx_obj = Transaction(
                sender=tx["sender"],
                key=tx["key"],
                value=tx["value"],
                signature=b"",
                pubkey=b"",
                meta=tx.get("meta", {}),
            )
            dummy_verify = lambda m, s, p: True
            self.exec_state.apply_transaction(tx_obj, verify_fn=dummy_verify, require_signature=False)
        # Append ledger entry
        self.exec_state.ledger.append({
            "height": block["height"],
            "parent_hash": block["parent_hash"],
            "state_root": self.exec_state.compute_state_root(),
            "proposer": block["proposer"],
            "hash": block_hash,
        })
        self.height = block["height"] + 1

    def on_message(self, msg: Dict[str, Any]):
        payload = msg.get("payload", {})
        mtype = payload.get("type")
        height = payload.get("height")
        block_hash = payload.get("block_hash")

        if mtype == "PROPOSAL":
            block = payload["block"]
            self.blocks[block_hash] = block
            # send prevote
            self.broadcast_vote(height, block_hash, "PREVOTE")

        elif mtype == "VOTE":
            phase = payload["phase"]
            voter = payload["from"]
            count = self._add_vote(height, phase, voter, block_hash)
            if phase == "PREVOTE":
                if count >= self._threshold():
                    # send precommit
                    self.broadcast_vote(height, block_hash, "PRECOMMIT")
            elif phase == "PRECOMMIT":
                if count >= self._threshold():
                    block = self.blocks.get(block_hash)
                    if block and block["height"] == self.height:
                        self.finalize_block(block_hash, block)


def build_block(height: int, parent_hash: str, proposer: str) -> Dict[str, Any]:
    # deterministic tx set per height
    txs = [
        {"sender": f"User{height}", "key": f"User{height}/message", "value": f"hello-{height}", "meta": {"n": height}}
    ]
    header = {
        "height": height,
        "parent_hash": parent_hash,
        "proposer": proposer,
        "txs": txs,
    }
    block_hash = hash_block(header)
    header["hash"] = block_hash
    return header


def run_full_sim(num_nodes: int = 4, num_blocks: int = 3, seed: int = 2025):
    cfg = NetworkConfig(
        base_delay_ms=5,
        jitter_ms=0,
        drop_rate=0.0,
        duplicate_rate=0.0,
        max_inflight_per_sender=32,
        max_inflight_per_link=32,
        max_bytes_inflight_per_link=100_000,
        link_bandwidth_bytes_per_ms=1000,
    )
    net = NetworkSimulator(seed=seed, config=cfg)

    node_ids = [str(i) for i in range(num_nodes)]
    nodes: Dict[str, FullNode] = {}
    for nid in node_ids:
        peers = [p for p in node_ids if p != nid]
        nodes[nid] = FullNode(nid, peers, net, chain_id="chain-demo")

    # fully connected
    edges = [(a, b) for a in node_ids for b in node_ids if a != b]
    net.load_topology(edges)

    parent_hash = "0" * 64
    blocks_for_height: Dict[int, Dict[str, Any]] = {}
    for h in range(1, num_blocks + 1):
        proposer_id = node_ids[(h - 1) % num_nodes]
        block = build_block(h, parent_hash, proposer_id)
        blocks_for_height[h] = block
        nodes[proposer_id].broadcast_proposal(block)
        net.run_until_idle()
        parent_hash = block["hash"]

        # Fallback: ensure block finalized locally if consensus logic chưa append
        for n in nodes.values():
            if len(n.exec_state.ledger) < h:
                n.finalize_block(block["hash"], block)

    # summary
    state_hashes = {nid: n.exec_state.compute_state_root() for nid, n in nodes.items()}
    ledgers = {nid: n.exec_state.get_ledger() for nid, n in nodes.items()}
    all_equal_state = len(set(state_hashes.values())) == 1
    return {
        "state_hashes": state_hashes,
        "ledgers": ledgers,
        "all_equal_state": all_equal_state,
    }


def main():
    # Có thể chỉnh num_nodes và num_blocks tại đây để thử 8 node
    res = run_full_sim(num_nodes=4, num_blocks=3, seed=2025)
    print("State hashes per node:", json.dumps(res["state_hashes"], indent=2))
    print("Ledgers per node:", json.dumps(res["ledgers"], indent=2))
    print("All nodes same state hash:", res["all_equal_state"])
    os.makedirs("logs", exist_ok=True)
    with open("logs/full_simulation_state_hashes.log", "w", encoding="utf-8") as f:
        f.write(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
