import unittest
import sys
import os

# Thêm thư mục gốc vào đường dẫn để Python tìm thấy 'src'
# Đoạn này giúp import được src.consensus.messages dù đang đứng ở folder tests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.consensus.messages import Vote
from src.consensus.engine import ConsensusEngine

class TestConsensusEngine(unittest.TestCase):
    
    def setUp(self):
        """
        Hàm này chạy trước MỖI bài test để reset lại môi trường.
        Giả lập mạng lưới 4 node.
        Ngưỡng quá bán (Threshold) = (4 * 2) // 3 + 1 = 3 phiếu.
        """
        self.total_nodes = 4
        self.engine = ConsensusEngine(my_id=0, total_nodes=self.total_nodes)
        self.block_hash = "hash_cua_block_so_1"
        self.height = 1

    def test_prevote_quorum_reached(self):
        """
        Kịch bản: Bơm lần lượt 3 phiếu PREVOTE.
        Kỳ vọng: 
            - Phiếu 1, 2: Không có gì xảy ra (None).
            - Phiếu 3: Trả về tín hiệu "SEND_PRECOMMIT".
        """
        # Node 1 gửi phiếu
        vote1 = Vote(validator_id=1, height=self.height, block_hash=self.block_hash, phase="PREVOTE")
        res1 = self.engine.process_vote(vote1)
        self.assertIsNone(res1, "Mới 1 phiếu, chưa được làm gì cả")

        # Node 2 gửi phiếu
        vote2 = Vote(validator_id=2, height=self.height, block_hash=self.block_hash, phase="PREVOTE")
        res2 = self.engine.process_vote(vote2)
        self.assertIsNone(res2, "Mới 2 phiếu, chưa được làm gì cả")

        # Node 3 gửi phiếu (Phiếu quyết định)
        vote3 = Vote(validator_id=3, height=self.height, block_hash=self.block_hash, phase="PREVOTE")
        res3 = self.engine.process_vote(vote3)
        
        # KIỂM TRA QUAN TRỌNG: Phải nhận được lệnh gửi Precommit
        self.assertEqual(res3, "SEND_PRECOMMIT", "Khi đủ 3 Prevote, engine phải ra lệnh gửi Precommit")

    def test_duplicate_vote_ignored(self):
        """
        Kịch bản: Một node gửi lặp lại cùng 1 phiếu.
        Kỳ vọng: Số lượng phiếu đếm được không thay đổi.
        """
        vote = Vote(validator_id=1, height=self.height, block_hash=self.block_hash, phase="PREVOTE")
        
        # Gửi lần 1
        self.engine.process_vote(vote)
        count_1 = len(self.engine.votes[self.height]["PREVOTE"][self.block_hash])
        
        # Gửi lần 2 (Replay attack / Mạng lag gửi lại)
        self.engine.process_vote(vote)
        count_2 = len(self.engine.votes[self.height]["PREVOTE"][self.block_hash])
        
        self.assertEqual(count_1, count_2, "Số lượng phiếu KHÔNG được tăng khi nhận phiếu trùng lặp")
        self.assertEqual(count_1, 1, "Tổng phiếu phải là 1")

    def test_precommit_finalization(self):
        """
        Kịch bản: Bơm lần lượt 3 phiếu PRECOMMIT.
        Kỳ vọng: Phiếu thứ 3 sẽ kích hoạt sự kiện "FINALIZE_BLOCK".
        """
        # Node 1 gửi Precommit
        v1 = Vote(validator_id=1, height=self.height, block_hash=self.block_hash, phase="PRECOMMIT")
        self.assertIsNone(self.engine.process_vote(v1))

        # Node 2 gửi Precommit
        v2 = Vote(validator_id=2, height=self.height, block_hash=self.block_hash, phase="PRECOMMIT")
        self.assertIsNone(self.engine.process_vote(v2))

        # Node 3 gửi Precommit (Phiếu quyết định)
        v3 = Vote(validator_id=3, height=self.height, block_hash=self.block_hash, phase="PRECOMMIT")
        res_final = self.engine.process_vote(v3)
        
        # KIỂM TRA QUAN TRỌNG: Block phải được Finalize
        self.assertEqual(res_final, "FINALIZE_BLOCK", "Khi đủ 3 Precommit, engine phải ra lệnh Finalize Block")

        # Kiểm tra phụ: Đảm bảo bộ đếm bên trong đúng là 3
        votes_count = len(self.engine.votes[self.height]["PRECOMMIT"][self.block_hash])
        self.assertEqual(votes_count, 3)

if __name__ == '__main__':
    unittest.main()