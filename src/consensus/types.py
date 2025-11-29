from dataclasses import dataclass
from typing import Optional


@dataclass
class Vote:
    height: int
    round: int 
    block_id: Optional[str]
    vote_type: str
    validator: str 
    chain_id: str
    
@dataclass
class Proposal:
    height: int
    round: int
    block_id: str
    proposer: str
    
@dataclass
class BlockHeader:
    block_id: str
    height: int
    proposer: str
    timestamp: float