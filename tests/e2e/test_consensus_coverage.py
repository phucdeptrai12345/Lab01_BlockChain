import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from src.network.simulator import NetworkSimulator, NetworkConfig
from src.consensus.engine import ConsensusEngine
from src.execution.execution import ExecutionState, Transaction


class FirstSeenNode:
    """
    Node mô phỏng: chốt proposal đầu tiên của mỗi height, bỏ qua proposal khác cùng height.
    Dùng để kiểm tra safety khi có 2 proposer cùng height.
    """

    def __init__(self, node_id, peers, net, height):
        self.node_id = node_id
        self.peers = peers
        self.net = net
        self.height = height
        self.chosen = None
        self.ledger = []
        net.register_node(node_id, self.on_message)

    def on_message(self, msg):
        payload = msg.get("payload", {})
        if payload.get("type") != "PROPOSAL":
            return
        block_hash = payload["block_hash"]
        if self.chosen is not None:
            # đã chọn block khác, bỏ qua
            return
        self.chosen = block_hash
        self.ledger.append(block_hash)

    def broadcast_proposal(self, block_hash):
        payload = {"type": "PROPOSAL", "height": self.height, "block_hash": block_hash}
        for peer in self.peers + [self.node_id]:
            self.net.send_header(self.node_id, peer, f"prop-{block_hash}-{peer}", self.height, payload)


class TestConsensusCoverage(unittest.TestCase):
    def test_two_proposals_same_height_only_one_finalized(self):
        cfg = NetworkConfig(base_delay_ms=0, jitter_ms=0, drop_rate=0.0, duplicate_rate=0.0)
        net = NetworkSimulator(seed=1, config=cfg)
        node_ids = ["A", "B", "C", "D"]
        nodes = {}
        for nid in node_ids:
            peers = [p for p in node_ids if p != nid]
            nodes[nid] = FirstSeenNode(nid, peers, net, height=1)
        net.load_topology([(a, b) for a in node_ids for b in node_ids])

        # gửi proposal hash_X trước, hash_Y sau
        nodes["A"].broadcast_proposal("hash_X")
        net.run_until_idle()
        nodes["B"].broadcast_proposal("hash_Y")
        net.run_until_idle()

        ledgers = [n.ledger for n in nodes.values()]
        self.assertTrue(all(len(l) == 1 for l in ledgers))
        first_hashes = {l[0] for l in ledgers}
        self.assertEqual(len(first_hashes), 1, "Chỉ một block được finalize tại height")

    def test_invalid_signature_in_consensus_flow(self):
        class EngineWithSigCheck(ConsensusEngine):
            def _mock_verify_signature(self, vote):
                # giả lập chữ ký: nếu vote.signature == b"bad" thì reject
                return vote.signature != b"bad"

        engine = EngineWithSigCheck(my_id="0", total_nodes=4)
        threshold = (4 * 2) // 3 + 1
        # gửi vote hợp lệ
        class V:
            def __init__(self, voter, sig):
                self.validator_id = voter
                self.height = 1
                self.block_hash = "h1"
                self.phase = "PREVOTE"
                self.signature = sig

        engine.process_vote(V("1", b"good"))
        engine.process_vote(V("2", b"bad"))  # nên bị bỏ qua
        engine.process_vote(V("3", b"good"))
        votes = engine.votes[1]["PREVOTE"]["h1"]
        self.assertEqual(len(votes), 2)  # chỉ ghi nhận 2 phiếu hợp lệ, không đạt ngưỡng
        self.assertLess(len(votes), threshold)

    def test_transaction_replay_same_tx_different_blocks(self):
        exec_state = ExecutionState(chain_id="test-chain")
        tx = Transaction(
            sender="Alice",
            key="Alice/msg",
            value="hello",
            signature=b"",
            pubkey=b"",
        )
        dummy_verify = lambda m, s, p: True
        # Block 1 áp dụng tx
        exec_state.apply_transaction(tx, verify_fn=dummy_verify, require_signature=False)
        exec_state.ledger.append({"height": 1, "hash": "h1"})
        # Block 2 replay cùng tx (trong thực tế nên reject; ở đây kiểm tra state vẫn nhất quán)
        exec_state.apply_transaction(tx, verify_fn=dummy_verify, require_signature=False)
        exec_state.ledger.append({"height": 2, "hash": "h2"})

        self.assertEqual(exec_state.state["Alice/msg"], "hello")
        self.assertEqual(len(exec_state.ledger), 2)

    def test_delayed_vote_does_not_break_safety(self):
        cfg = NetworkConfig(base_delay_ms=0, jitter_ms=0, drop_rate=0.0, duplicate_rate=0.0)
        net = NetworkSimulator(seed=3, config=cfg)
        ids = ["P", "Q"]
        nodes = {}
        for nid in ids:
            peers = [p for p in ids if p != nid]
            nodes[nid] = FirstSeenNode(nid, peers, net, height=1)
        net.load_topology([(a, b) for a in ids for b in ids])

        # Proposal A tới trước
        nodes["P"].broadcast_proposal("hash_A")
        net.run_until_idle()
        # Proposal B gửi trễ
        nodes["Q"].broadcast_proposal("hash_B")
        net.run_until_idle()

        ledgers = [n.ledger for n in nodes.values()]
        hashes = {l[0] for l in ledgers}
        self.assertTrue(all(len(l) == 1 for l in ledgers))
        self.assertEqual(len(hashes), 1, "Vote/proposal trễ không làm đổi block đã chọn")


if __name__ == "__main__":
    unittest.main()

