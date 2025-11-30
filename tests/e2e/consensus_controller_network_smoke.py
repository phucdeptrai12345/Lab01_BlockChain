"""
Smoke test tích hợp ConsensusController + NetworkConsensusHelper + NetworkSimulator.
- 4 node, 1 height.
- Proposer round-robin, gửi proposal -> prevote -> precommit qua network.
- Kiểm tra tất cả node commit cùng block hash.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from src.consensus.controller import ConsensusController
from src.consensus.helper import NetworkConsensusHelper
from src.network.simulator import NetworkSimulator, NetworkConfig


class ControllerNode:
    def __init__(self, node_id, peers, network):
        self.helper = NetworkConsensusHelper(node_id, peers, network)
        # auto_advance=False để tránh vòng lặp nhiều height trong smoke test
        self.controller = ConsensusController(node_id, self.helper, auto_advance=False)
        self.helper.set_controller(self.controller)
        network.register_node(node_id, self.helper.on_message)
        self.node_id = node_id


def main():
    cfg = NetworkConfig(base_delay_ms=5, jitter_ms=0, drop_rate=0.0, duplicate_rate=0.0)
    net = NetworkSimulator(seed=123, config=cfg)

    node_ids = ["0", "1", "2", "3"]
    nodes = {}
    for nid in node_ids:
        peers = [p for p in node_ids if p != nid]
        nodes[nid] = ControllerNode(nid, peers, net)

    # Cho phép self-edge để node nhận được vote của chính nó (do helper gửi cả cho self)
    edges = [(a, b) for a in node_ids for b in node_ids]
    net.load_topology(edges)

    # Start round 0 cho tất cả node
    for n in nodes.values():
        n.controller.start_round(0)

    net.run_until_idle()

    ledgers = {nid: n.helper.ledger for nid, n in nodes.items()}
    first_hash = None
    all_same = True
    for l in ledgers.values():
        if not l:
            all_same = False
            break
        h = l[0]["hash"]
        if first_hash is None:
            first_hash = h
        elif h != first_hash:
            all_same = False
            break

    print("Ledgers:", ledgers)
    print("All nodes have same first block hash:", all_same)
    if not all_same:
        print("Consensus controller network smoke FAILED")
        sys.exit(1)
    print("Consensus controller network smoke PASSED")


if __name__ == "__main__":
    main()

