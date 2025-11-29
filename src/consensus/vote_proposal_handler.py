from typing import Optional, Callable, Any
from .vote_set import VoteSet
from .block_store import BlockStore
from .proposal_store import ProposalStore
from .message_validator import MessageValidator
from .types import Vote, Proposal, BlockHeader, Block
from src.consensus.constants import NIL_BLOCK_HASH


class VoteProposalHandler:

    def __init__(self, chain_id: str, validators: list[str]):
        self.vote_set = VoteSet()
        self.block_store = BlockStore()
        self.proposal_store = ProposalStore()
        self.validator = MessageValidator(chain_id)

        self.validators = validators  
        self.chain_id = chain_id

        self.cb_proposal_ready: Optional[Callable[[Any], None]] = None
        
    def on_block_header(self, header: BlockHeader):
        if not self.validator.validate_block(header):
            return False
        self.block_store.save(header)
        return True

    def on_proposal(self, proposal: Proposal):
        block = self.block_store.get(proposal.block_id)
        if not block:
            return False

        if not self.validator.validate_proposal(proposal, block):
            return False

        self.proposal_store.save(proposal)

        if self.cb_proposal_ready:
            self.cb_proposal_ready(block)

        return True

    def on_vote(self, vote: Vote):
        if not self.validator.validate_vote(vote):
            return False
        if self.vote_set.has_vote(vote):
            return False
        return self.vote_set.add_vote(vote)
    
    def get_proposer(self, height: int, round: int) -> str:
        idx = (height + round) % len(self.validators)
        return self.validators[idx]

    def create_proposal(self, height: int, round: int) -> Block:
        
        parent = self.block_store.get_last_block_hash()
        block = Block(
            height=height,
            round=round,
            parent_hash=parent,
            hash=f"block-{height}-{round}",
            txs=["tx1", "tx2"]
        )
        self.block_store.save(block)
        return block

    def broadcast_proposal(self, height: int, round: int, block: Block):
        proposal = Proposal(
            height=height,
            round=round,
            block_id=block.hash,
            proposer_id="?",
            signature="dummy"
        )
        print(f"[BROADCAST] Proposal {proposal.block_id}")

    def broadcast_vote(self, height: int, round: int, vote_type: str, block_hash: str):
        vote = Vote(
            height=height,
            round=round,
            vote_type=vote_type,
            block_id=block_hash,
            validator="local-node",
            chain_id=self.chain_id
        )
        print(f"[BROADCAST] VOTE {vote_type} -> {block_hash}")
        self.vote_set.add_vote(vote)

    def schedule_timeout(self, duration: float, step):
        print(f"[TIMER] Schedule timeout {step} in {duration}s")

    def get_block_by_hash(self, h: str) -> Optional[Block]:
        return self.block_store.get(h)

    def commit_block(self, block: Block):
        print(f"[LEDGER] Committing block: {block.hash}")
        
    def get_votes(self, height: int, round: int, vote_type: str):
        return self.vote_set.get_votes(height, round, vote_type)

    def count_votes_for_block(self, height: int, round: int, vote_type: str, block_id: str):
        return self.vote_set.count_for_block(height, round, vote_type, block_id)
