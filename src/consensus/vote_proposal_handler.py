# vote_proposal_handler.py
from typing import Optional, Callable
from .vote_set import VoteSet
from .block_store import BlockStore
from .proposal_store import ProposalStore
from .message_validator import MessageValidator
from .types import Vote, Proposal, BlockHeader


class VoteProposalHandler:

    def __init__(self, chain_id: str):
        self.vote_set = VoteSet()
        self.block_store = BlockStore()
        self.proposal_store = ProposalStore()
        self.validator = MessageValidator(chain_id)

        self.cb_proposal_ready: Optional[Callable[[int, int], None]] = None

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
            self.cb_proposal_ready(proposal.height, proposal.round)

        return True

    def on_vote(self, vote: Vote):
        if not self.validator.validate_vote(vote):
            return False

        if self.vote_set.has_vote(vote):
            return False 

        return self.vote_set.add_vote(vote)

    def get_proposal(self, height: int, round: int) -> Optional[Proposal]:
        return self.proposal_store.get(height, round)

    def get_votes(self, height: int, round: int, vote_type: str):
        return self.vote_set.get_votes(height, round, vote_type)

    def count_votes_for_block(self, height: int, round: int, vote_type: str, block_id: str):
        return self.vote_set.count_for_block(height, round, vote_type, block_id)

    def create_vote(self, height: int, round: int, block_id: Optional[str],
                    vote_type: str, validator_id: str):

        vote = Vote(
            height=height,
            round=round,
            block_id=block_id,
            vote_type=vote_type,
            validator=validator_id,
            chain_id=self.validator.chain_id
        )

        if not self.validator.validate_vote(vote):
            return None

        self.vote_set.add_vote(vote)
        return vote
