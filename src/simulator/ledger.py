from typing import List, Optional

from src.simulator.block import Block, compute_block_hash


class Ledger:
    """
    Sổ cái lưu các block đã FINALIZED, theo đúng thứ tự từ genesis -> latest.
    """
    def __init__(self):
        self._blocks: List[Block] = []

    def height(self) -> int:
        """
        Trả về số block đã finalized.
        Genesis (chưa có block) = 0.
        """
        return len(self._blocks)

    def last_block(self) -> Optional[Block]:
        """
        Trả về block cuối cùng (nếu có).
        """
        if not self._blocks:
            return None
        return self._blocks[-1]

    def last_hash(self) -> str:
        """
        Hash của block cuối cùng.
        Nếu chưa có block nào -> trả về '0' * 64 (giống genesis parent_hash).
        """
        if not self._blocks:
            return "0" * 64
        return compute_block_hash(self._blocks[-1].header)

    def append_finalized_block(self, block: Block) -> None:
        """
        Thêm 1 block mới đã FINALIZED vào ledger.
        Không kiểm tra signature ở đây – giả sử consensus đã validate.
        """
        # Có thể thêm check đơn giản về parent cho chắc:
        expected_parent = self.last_hash()
        if block.header.parent_hash != expected_parent:
            print("Warning: appending block with unexpected parent hash")
        self._blocks.append(block)

    def all_blocks(self) -> List[Block]:
        """
        Trả về list copy của các block (để đọc).
        """
        return list(self._blocks)
