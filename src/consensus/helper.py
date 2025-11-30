import hashlib
import json
from typing import Any, Dict, List, Optional, Set

from src.consensus.constants import ConsensusStep


def _deterministic_hash(obj: Any) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class NetworkConsensusHelper:
    """
    Bridge giữa ConsensusController và NetworkSimulator.
    - Tạo proposal, gửi/nhận proposal & vote qua network.
    - Đếm quorum và gọi ngược controller.on_majority_prevote/precommit.
    - Quản lý block store, ledger tối giản.
    """

    def __init__(self, node_id: str, peers: List[str], network):
        self.node_id = node_id
        self.peers = peers
        self.network = network
        self.controller = None  # sẽ set từ outside
        self.block_store: Dict[str, Any] = {}
        self.ledger: List[Dict[str, Any]] = []
        self.votes: Dict[int, Dict[str, Dict[str, Set[str]]]] = {}  # votes[height][phase][block_hash] = set(ids)

    def set_controller(self, controller):
        self.controller = controller

    # Interface expected by ConsensusController --------------------------------
    def get_proposer(self, height: int, round_num: int) -> str:
        nodes = sorted(self.peers + [self.node_id])
        return nodes[(height + round_num) % len(nodes)]

    def create_proposal(self, height: int, round_num: int):
        block = {
            "height": height,
            "round": round_num,
            "parent_hash": self.ledger[-1]["hash"] if self.ledger else "0" * 64,
            "proposer": self.node_id,
            "txs": [
                {"sender": f"User{height}", "key": f"User{height}/msg", "value": f"hello-{height}"}
            ],
        }
        block["hash"] = _deterministic_hash(block)
        self.block_store[block["hash"]] = block
        return type("Proposal", (), block)

    def schedule_timeout(self, timeout_sec: float, step: ConsensusStep):
        return

    def broadcast_proposal(self, height: int, round_num: int, block: Any):
        payload = {
            "type": "PROPOSAL",
            "height": height,
            "round": round_num,
            "block_hash": block.hash,
            "block": block.__dict__,
        }
        for peer in self.peers + [self.node_id]:
            self.network.send_header(
                sender=self.node_id,
                receiver=peer,
                header_id=f"proposal-{height}-{round_num}-{self.node_id}-{peer}",
                height=height,
                payload=payload,
            )

    def broadcast_vote(self, height: int, round: int, vote_type: ConsensusStep, block_hash: Optional[str]):
        payload = {
            "type": "VOTE",
            "height": height,
            "round": round,
            "block_hash": block_hash,
            "phase": vote_type.value,
            "from": self.node_id,
        }
        for peer in self.peers + [self.node_id]:
            self.network.send_header(
                sender=self.node_id,
                receiver=peer,
                header_id=f"vote-{vote_type.value}-{height}-{self.node_id}-{peer}",
                height=height,
                payload=payload,
            )

    def get_block_by_hash(self, block_hash: str):
        block = self.block_store.get(block_hash)
        if block is None:
            return None
        return type("Proposal", (), block)

    def commit_block(self, block_obj: Any):
        header = {
            "height": block_obj.height,
            "parent_hash": block_obj.parent_hash,
            "state_root": getattr(block_obj, "state_root", ""),
            "proposer": block_obj.proposer,
            "hash": block_obj.hash,
        }
        self.ledger.append(header)

    # Message handling ---------------------------------------------------------
    def on_message(self, msg: Dict[str, Any]):
        payload = msg.get("payload", {})
        mtype = payload.get("type")
        if mtype == "PROPOSAL":
            block_dict = payload.get("block")
            if block_dict:
                block_hash = payload.get("block_hash")
                block_copy = dict(block_dict)
                block_copy["hash"] = block_hash
                self.block_store[block_hash] = block_copy
                if self.controller:
                    self.controller.on_proposal_received(type("Proposal", (), block_copy))
        elif mtype == "VOTE":
            height = payload.get("height")
            phase = payload.get("phase")
            block_hash = payload.get("block_hash")
            voter = payload.get("from")
            if not (height and phase and block_hash and voter):
                return
            count = self._record_vote(height, phase, block_hash, voter)
            threshold = (len(self.peers) + 1) * 2 // 3 + 1
            if count >= threshold and self.controller:
                if phase == ConsensusStep.PREVOTE.value:
                    if self.controller.current_step != ConsensusStep.PREVOTE:
                        self.controller.current_step = ConsensusStep.PREVOTE
                    self.controller.on_majority_prevote(block_hash)
                elif phase == ConsensusStep.PRECOMMIT.value:
                    if self.controller.current_step != ConsensusStep.PRECOMMIT:
                        self.controller.current_step = ConsensusStep.PRECOMMIT
                    self.controller.on_majority_precommit(block_hash)

    def _record_vote(self, height: int, phase: str, block_hash: str, voter: str) -> int:
        self.votes.setdefault(height, {}).setdefault(phase, {}).setdefault(block_hash, set()).add(voter)
        count = len(self.votes[height][phase][block_hash])
        print(f"[{self.node_id}] Votes {phase} for {block_hash[:6]}... count={count}")
        return count

