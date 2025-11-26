class Vote:
    def __init__(self, validator_id, height, block_hash, phase, signature=None):
        self.validator_id = validator_id  # Ai bầu? [cite: 41]
        self.height = height              # Bầu cho block độ cao bao nhiêu? [cite: 26, 46]
        self.block_hash = block_hash      # Mã băm của block [cite: 26, 46]
        self.phase = phase                # 'PREVOTE' hoặc 'PRECOMMIT' [cite: 27]
        self.signature = signature        # Chữ ký số [cite: 56]

    def __repr__(self):
        return f"Vote(signer={self.validator_id}, height={self.height}, phase={self.phase}, hash={self.block_hash[:6]}...)"

    # Hàm giả lập để lấy dữ liệu cần ký (Sau này module Crypto sẽ dùng cái này)
    def to_bytes(self):
        # Đề bài yêu cầu context string "VOTE: chain_id" [cite: 56]
        # Hiện tại bạn cứ trả về chuỗi đơn giản để test logic trước
        return f"VOTE:{self.height}:{self.block_hash}:{self.phase}".encode()