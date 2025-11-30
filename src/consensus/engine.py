from collections import defaultdict


class ConsensusEngine:
    """
    Engine tối giản: đếm phiếu prevote/precommit, trả về tín hiệu khi đạt quorum.
    """

    def __init__(self, my_id, total_nodes):
        self.my_id = my_id
        self.total_nodes = total_nodes
        # votes[height][phase][block_hash] = set(validator_ids)
        self.votes = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    def process_vote(self, vote):
        if not self._mock_verify_signature(vote):
            return

        if vote.validator_id in self.votes[vote.height][vote.phase][vote.block_hash]:
            return

        self.votes[vote.height][vote.phase][vote.block_hash].add(vote.validator_id)

        threshold = (self.total_nodes * 2) // 3 + 1
        count = len(self.votes[vote.height][vote.phase][vote.block_hash])

        if count >= threshold:
            return self._on_quorum_reached(vote.height, vote.phase, vote.block_hash)
        return None

    def _on_quorum_reached(self, height, phase, block_hash):
        if phase == "PREVOTE":
            return "SEND_PRECOMMIT"
        elif phase == "PRECOMMIT":
            return "FINALIZE_BLOCK"
        return None

    def _mock_verify_signature(self, vote):
        return True

