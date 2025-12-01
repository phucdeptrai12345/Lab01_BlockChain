from typing import List, Optional,Dict

from src.simulator.block import Block, compute_block_hash


class Ledger:
    def __init__(self):
        self._blocks: List[Block] = []
        self._block_map: Dict[str, Block] = {}

    def height(self) -> int:
        return len(self._blocks)

    def last_block(self) -> Optional[Block]:
        if not self._blocks:
            return None
        return self._blocks[-1]

    def last_hash(self) -> str:
        if not self._blocks:
            return "0" * 64
        return compute_block_hash(self._blocks[-1].header)

    def append_finalized_block(self, block: Block) -> bool:
        expected_parent = self.last_hash()
        if block.header.parent_hash != expected_parent:
            print(f"[Ledger] Error: Block parent {block.header.parent_hash[:8]} != Last hash {expected_parent[:8]}")
            return False
        self._blocks.append(block)
        b_hash = compute_block_hash(block.header)
        self._block_map[b_hash] = block
        return True
    def get_block_by_height(self, height: int) -> Optional[Block]:
        if 0 <= height < len(self._blocks):
            return self._blocks[height]
        return None
    def get_block_by_hash(self, b_hash: str) -> Optional[Block]:
        return self._block_map.get(b_hash)

    def all_blocks(self) -> List[Block]:
        return list(self._blocks)
