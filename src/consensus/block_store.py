from typing import Dict
from .types import BlockHeader


class BlockStore:

    def __init__(self):
        self.blocks: Dict[str, BlockHeader] = {}

    def save(self, header: BlockHeader):
        self.blocks[header.block_id] = header

    def get(self, block_id: str):
        return self.blocks.get(block_id)
