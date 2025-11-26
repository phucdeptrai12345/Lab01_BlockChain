from collections import defaultdict

class ConsensusEngine:
    def __init__(self, my_id, total_nodes):
        self.my_id = my_id
        self.total_nodes = total_nodes
        # Kho chứa phiếu: votes[height][phase][block_hash] = set(validator_ids)
        self.votes = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    def process_vote(self, vote):
        """
        Hàm này nhận một object Vote từ Bước 1
        """
        # 1. MOCK: Giả vờ kiểm tra chữ ký (Sau này gọi src.crypto ở đây) [cite: 86]
        if not self._mock_verify_signature(vote):
            print(f"Log: Chữ ký không hợp lệ từ {vote.validator_id}")
            return

        # 2. Lưu phiếu (chống duplicate vote từ 1 người)
        if vote.validator_id in self.votes[vote.height][vote.phase][vote.block_hash]:
            return # Người này đã bầu rồi, bỏ qua [cite: 93]
        
        self.votes[vote.height][vote.phase][vote.block_hash].add(vote.validator_id)
        
        # 3. Kiểm tra ngưỡng quá bán (Strict Majority > 2/3) [cite: 71]
        threshold = (self.total_nodes * 2) // 3 + 1
        count = len(self.votes[vote.height][vote.phase][vote.block_hash])

        print(f"Node {self.my_id} received {vote.phase} for block {vote.block_hash[:4]}... Total: {count}/{self.total_nodes}")

        if count >= threshold:
            return self._on_quorum_reached(vote.height, vote.phase, vote.block_hash)
        
        return None

    def _on_quorum_reached(self, height, phase, block_hash):
        """
        [cite_start]Xử lý khi đã đủ số phiếu (Quorum) [cite: 71]
        """
        if phase == "PREVOTE":
            print(f"==> Đạt đa số PREVOTE tại height {height}. Chuẩn bị gửi PRECOMMIT.")
            # TRẢ VỀ giá trị để Unit Test bắt được
            return "SEND_PRECOMMIT" 

        elif phase == "PRECOMMIT":
            print(f"==> Đạt đa số PRECOMMIT tại height {height}. BLOCK FINALIZED!")
            # TRẢ VỀ giá trị để Unit Test bắt được
            return "FINALIZE_BLOCK"
            
        return None

    def _mock_verify_signature(self, vote):
        # Tạm thời luôn đúng để test logic đếm phiếu
        return True