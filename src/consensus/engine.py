from collections import defaultdict


class ConsensusEngine:
    """
    Minimal quorum-based prevote/precommit engine.
    """

    def __init__(self, my_id, total_nodes):
        self.my_id = my_id
        self.total_nodes = total_nodes
        # votes[height][phase][block_hash] = set(validator_ids)
        self.votes = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    def process_vote(self, vote):
        """
        Process a Vote object.
        Returns:
            - "SEND_PRECOMMIT" when prevote quorum reached
            - "FINALIZE_BLOCK" when precommit quorum reached
            - None otherwise
        """
        # Mock signature check (placeholder for real crypto)
        if not self._mock_verify_signature(vote):
            print(f"Log: Invalid signature from {vote.validator_id}")
            return

        # Ignore duplicate from same validator
        if vote.validator_id in self.votes[vote.height][vote.phase][vote.block_hash]:
            return

        self.votes[vote.height][vote.phase][vote.block_hash].add(vote.validator_id)

        threshold = (self.total_nodes * 2) // 3 + 1
        count = len(self.votes[vote.height][vote.phase][vote.block_hash])

        print(f"Node {self.my_id} received {vote.phase} for block {vote.block_hash[:4]}... Total: {count}/{self.total_nodes}")

        if count >= threshold:
            return self._on_quorum_reached(vote.height, vote.phase, vote.block_hash)

        return None

    def _on_quorum_reached(self, height, phase, block_hash):
        if phase == "PREVOTE":
            print(f"==> Reached PREVOTE quorum at height {height}. Prepare PRECOMMIT.")
            return "SEND_PRECOMMIT"
        elif phase == "PRECOMMIT":
            print(f"==> Reached PRECOMMIT quorum at height {height}. BLOCK FINALIZED!")
            return "FINALIZE_BLOCK"
        return None

    def _mock_verify_signature(self, vote):
        return True
