from typing import List, Optional,Dict

from src.simulator.block import Block, compute_block_hash


class Ledger:
    """
    Sổ cái lưu các block đã FINALIZED, theo đúng thứ tự từ genesis -> latest.
    """
    def __init__(self):
        self._blocks: List[Block] = []
        self._block_map: Dict[str, Block] = {}

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

    def append_finalized_block(self, block: Block) -> bool:
        """
        Thêm 1 block mới đã FINALIZED vào ledger.
        Không kiểm tra signature ở đây – giả sử consensus đã validate.
        """
        # Có thể thêm check đơn giản về parent cho chắc:
        expected_parent = self.last_hash()
        if block.header.parent_hash != expected_parent:
            print(f"[Ledger] Error: Block parent {block.header.parent_hash[:8]} != Last hash {expected_parent[:8]}")
            return False
        
        # Thêm vào list và map
        self._blocks.append(block)
        b_hash = compute_block_hash(block.header)
        self._block_map[b_hash] = block # Lưu vào map
        return True
    def get_block_by_height(self, height: int) -> Optional[Block]:
        if 0 <= height < len(self._blocks):
            return self._blocks[height]
        return None
    def get_block_by_hash(self, b_hash: str) -> Optional[Block]:
        return self._block_map.get(b_hash)

    def all_blocks(self) -> List[Block]:
        """
        Trả về list copy của các block (để đọc).
        """
        return list(self._blocks)
