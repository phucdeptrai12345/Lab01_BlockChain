class Vote:
    def __init__(self, validator_id, height, block_hash, phase, signature=None):
        self.validator_id = validator_id
        self.height = height
        self.block_hash = block_hash
        self.phase = phase
        self.signature = signature

    def to_bytes(self):
        return f"VOTE:{self.height}:{self.block_hash}:{self.phase}".encode()

