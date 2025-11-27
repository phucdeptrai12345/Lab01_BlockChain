from typing import Optional, Any
from src.consensus.constants import ConsensusStep

class ConsensusController:
    def __init__(self, node_id: str, helper: Any):
        """
        Khởi tạo bộ điều khiển đồng thuận.
        
        Args:
            node_id: Định danh của node hiện tại (ví dụ: public key hoặc ID).
            helper: Một đối tượng hỗ trợ (Interface) để giao tiếp với mạng/blockchain
                    (Người B sẽ implement phần này sau).
        """
        self.node_id = node_id
        self.helper = helper

        # --- State Variables (Biến trạng thái) ---
        # Chiều cao block hiện tại đang xử lý (Bắt đầu từ 1 hoặc theo chain)
        self.current_height: int = 1
        
        # Vòng đồng thuận hiện tại (Round). Nếu round thất bại, round sẽ tăng lên.
        self.current_round: int = 0
        
        # Bước hiện tại (PROPOSE, PREVOTE, hay PRECOMMIT)
        self.current_step: Optional[ConsensusStep] = None

        # --- Locking Mechanism (Cơ chế khóa - Rất quan trọng cho BFT) ---
        # Khi node đã vote cho một block ở một round nào đó, nó bị "khóa" vào block đó.
        # Điều này ngăn chặn việc node vote lung tung cho nhiều block khác nhau gây fork.
        
        # Block mà node đã lock (thường lưu hash hoặc object block đầy đủ)
        self.locked_block: Optional[Any] = None
        
        # Round mà tại đó node đã lock block
        self.locked_round: int = -1

    def start_round(self, round_num: int):
        """
        Hàm khởi động một vòng đồng thuận mới.
        Sẽ được gọi khi bắt đầu height mới hoặc khi timeout round cũ.
        """
        print(f"--- Bắt đầu Round {round_num} tại Height {self.current_height} ---")
        self.current_round = round_num
        self.current_step = ConsensusStep.PROPOSE
        # Logic chuyển trạng thái sẽ nằm ở các giai đoạn sau

    # --- Placeholder Interfaces (Giả lập hành động gửi đi) ---
    # Các hàm này sẽ gọi self.helper để thực hiện tác vụ mạng thực tế sau này.

    def broadcast_proposal(self, block: Any):
        """Gửi đề xuất block mới cho toàn mạng (nếu mình là Proposer)"""
        print(f"[{self.node_id}] Đang phát tán Proposal cho Block {block}...")
        if self.helper:
            self.helper.broadcast_proposal(self.current_height, self.current_round, block)

    def broadcast_vote(self, vote_type: ConsensusStep, block_hash: Optional[str]):
        """Gửi vote (PREVOTE hoặc PRECOMMIT) cho mạng"""
        print(f"[{self.node_id}] Đang gửi {vote_type.value} cho BlockHash: {block_hash}")
        if self.helper:
            self.helper.broadcast_vote(
                height=self.current_height,
                round=self.current_round,
                vote_type=vote_type,
                block_hash=block_hash
            )

    def on_timeout(self, step: ConsensusStep):
        """Hàm xử lý khi hết thời gian chờ của một bước"""
        print(f"!!! Timeout tại bước {step.value} !!!")
        # Logic xử lý timeout (như chuyển sang round tiếp theo) sẽ code sau