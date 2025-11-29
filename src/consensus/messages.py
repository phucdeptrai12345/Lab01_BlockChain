class Vote:
    def __init__(self, validator_id, height, block_hash, phase, signature=None):
        self.validator_id = validator_id
        self.height = height
        self.block_hash = block_hash
        self.phase = phase  # "PREVOTE" or "PRECOMMIT"
        self.signature = signature

    def __repr__(self):
        return f"Vote(signer={self.validator_id}, height={self.height}, phase={self.phase}, hash={self.block_hash[:6]}...)"

    def to_bytes(self):
        """
        Bytes to sign (domain separation handled by caller).
        Currently simple encoding for logic tests.
        """
        return f"VOTE:{self.height}:{self.block_hash}:{self.phase}".encode()

