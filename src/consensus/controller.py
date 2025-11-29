from typing import Optional, Any
from src.consensus.constants import (
    ConsensusStep, 
    TIMEOUT_PROPOSE, 
    TIMEOUT_PREVOTE, 
    TIMEOUT_PRECOMMIT, 
    NIL_BLOCK_HASH
)

class ConsensusController:
    def __init__(self, node_id: str, helper: Any):
        """
        Khởi tạo bộ điều khiển đồng thuận.
        Args:
            node_id: Định danh của node hiện tại.
            helper: Interface giao tiếp với module khác (Người B implementation).
        """
        self.node_id = node_id
        self.helper = helper

        # --- State Variables ---
        self.current_height: int = 1
        self.current_round: int = 0
        self.current_step: Optional[ConsensusStep] = None

        # --- Locking Mechanism (Safety Rules) ---
        self.locked_block: Optional[Any] = None
        self.locked_round: int = -1

    def start_round(self, round_num: int):
        """
        Hàm khởi động một vòng đồng thuận mới.
        """
        print(f"--- [CONTROLLER] Bắt đầu Round {round_num} tại Height {self.current_height} ---")
        
        # 1. Cập nhật trạng thái đầu vòng
        self.current_round = round_num
        self.current_step = ConsensusStep.PROPOSE
        
        # 2. Xác định Proposer (Người B cung cấp logic tính toán)
        proposer_id = self.helper.get_proposer(self.current_height, self.current_round)
        
        if proposer_id == self.node_id:
            # TRƯỜNG HỢP: TÔI LÀ PROPOSER
            print(f"[{self.node_id}] Tôi là Proposer. Đang tạo đề xuất...")
            
            # Logic: Nếu đang bị lock block nào đó, phải đề xuất lại block đó (Proof of Lock)
            # Nếu không, tạo block mới từ pool giao dịch.
            if self.locked_block is not None:
                proposal_block = self.locked_block
                print(f"[{self.node_id}] Đề xuất lại Locked Block: {proposal_block.hash}")
            else:
                proposal_block = self.helper.create_proposal(self.current_height, self.current_round)
                print(f"[{self.node_id}] Đề xuất Block mới: {proposal_block.hash}")

            self.broadcast_proposal(proposal_block)
        
        else:
            # TRƯỜNG HỢP: TÔI LÀ VALIDATOR
            print(f"[{self.node_id}] Chờ Proposal từ {proposer_id}...")
            # Đặt hẹn giờ: Nếu quá thời gian mà không nhận được Proposal -> Vote NIL
            self.helper.schedule_timeout(TIMEOUT_PROPOSE, ConsensusStep.PROPOSE)

    def on_proposal_received(self, proposal_block: Any):
        """
        Callback từ Người B: Khi nhận được một Proposal hợp lệ.
        """
        # Chỉ xử lý nếu đang ở bước PROPOSE (tránh xử lý tin nhắn cũ/spam)
        if self.current_step != ConsensusStep.PROPOSE:
            return

        # --- SAFETY RULE: LOCKING CHECK [cite: 72] ---
        vote_hash = proposal_block.hash
        
        # Nếu tôi đã khóa một block khác với block đang được đề xuất
        if self.locked_block is not None and self.locked_block.hash != proposal_block.hash:
            print(f"[{self.node_id}] Proposal khác Locked Block -> Vote NIL")
            vote_hash = NIL_BLOCK_HASH
        
        # Chuyển sang bước PREVOTE
        self.current_step = ConsensusStep.PREVOTE
        
        # Gửi phiếu PREVOTE
        self.broadcast_vote(ConsensusStep.PREVOTE, vote_hash)
        
        # Đặt hẹn giờ cho bước PREVOTE
        self.helper.schedule_timeout(TIMEOUT_PREVOTE, ConsensusStep.PREVOTE)

    def on_majority_prevote(self, majority_block_hash: str):
        """
        Callback từ Người B: Khi đã thu thập đủ +2/3 phiếu PREVOTE.
        """
        # Chỉ xử lý khi đang ở bước PREVOTE
        if self.current_step != ConsensusStep.PREVOTE:
            return

        print(f"[{self.node_id}] Đạt đa số PREVOTE cho: {majority_block_hash}")

        # --- SAFETY RULE: UPDATE LOCK [cite: 71] ---
        # Nếu đa số đồng ý một block thực (không phải NIL), tôi sẽ khóa vào nó
        if majority_block_hash != NIL_BLOCK_HASH:
            # Nhờ helper lấy object block đầy đủ từ hash
            block_obj = self.helper.get_block_by_hash(majority_block_hash)
            self.locked_block = block_obj
            self.locked_round = self.current_round
            print(f"[{self.node_id}] Đã LOCK vào block {majority_block_hash}")

        # Chuyển sang bước PRECOMMIT
        self.current_step = ConsensusStep.PRECOMMIT
        
        # Gửi phiếu PRECOMMIT (Vote cho cái mà đa số đã chọn)
        self.broadcast_vote(ConsensusStep.PRECOMMIT, majority_block_hash)
        
        # Đặt hẹn giờ cho bước PRECOMMIT
        self.helper.schedule_timeout(TIMEOUT_PRECOMMIT, ConsensusStep.PRECOMMIT)

    def on_majority_precommit(self, majority_block_hash: str):
        """
        Callback từ Người B: Khi đã thu thập đủ +2/3 phiếu PRECOMMIT.
        """
        if self.current_step != ConsensusStep.PRECOMMIT:
            return
        
        if majority_block_hash != NIL_BLOCK_HASH:
            # --- HAPPY PATH: FINALIZATION [cite: 71, 78] ---
            print(f"[{self.node_id}] !!! CONSENSUS REACHED !!! Block {majority_block_hash} finalized.")
            
            # 1. Commit block vào Ledger
            block_obj = self.helper.get_block_by_hash(majority_block_hash)
            self.helper.commit_block(block_obj)
            
            # 2. Reset trạng thái Lock (đã xong việc, mở khóa)
            self.locked_block = None
            self.locked_round = -1
            
            # 3. Tăng Height và bắt đầu Height mới
            self.current_height += 1
            self.start_round(0)
            
        else:
            # --- UNHAPPY PATH: ROUND CHANGE [cite: 73] ---
            # Đa số đồng ý là "không đồng ý gì cả" (NIL) -> Sang vòng sau
            print(f"[{self.node_id}] Consensus thất bại (NIL). Chuyển sang Round {self.current_round + 1}")
            self.start_round(self.current_round + 1)

    def on_timeout(self, step: ConsensusStep):
        """
        Hàm xử lý khi hết thời gian chờ (Liveness Guarantee).
        """
        # Chỉ xử lý timeout nếu nó khớp với bước hiện tại
        if self.current_step != step:
            return

        print(f"[{self.node_id}] !!! TIMEOUT tại bước {step.value} !!!")

        if step == ConsensusStep.PROPOSE:
            # Hết giờ chờ Proposal -> Vote NIL và sang Prevote
            self.current_step = ConsensusStep.PREVOTE
            self.broadcast_vote(ConsensusStep.PREVOTE, NIL_BLOCK_HASH)
            self.helper.schedule_timeout(TIMEOUT_PREVOTE, ConsensusStep.PREVOTE)

        elif step == ConsensusStep.PREVOTE:
            # Hết giờ Prevote (không đủ phiếu đa số) -> Vote Precommit NIL
            self.current_step = ConsensusStep.PRECOMMIT
            self.broadcast_vote(ConsensusStep.PRECOMMIT, NIL_BLOCK_HASH)
            self.helper.schedule_timeout(TIMEOUT_PRECOMMIT, ConsensusStep.PRECOMMIT)

        elif step == ConsensusStep.PRECOMMIT:
            # Hết giờ Precommit (vẫn không chốt được) -> Sang vòng mới
            print(f"[{self.node_id}] Timeout Precommit -> Round Change")
            self.start_round(self.current_round + 1)

    # --- Các hàm Wrapper gọi Helper ---
    def broadcast_proposal(self, block: Any):
        if self.helper:
            self.helper.broadcast_proposal(self.current_height, self.current_round, block)

    def broadcast_vote(self, vote_type: ConsensusStep, block_hash: Optional[str]):
        if self.helper:
            self.helper.broadcast_vote(
                height=self.current_height,
                round=self.current_round,
                vote_type=vote_type,
                block_hash=block_hash
            )