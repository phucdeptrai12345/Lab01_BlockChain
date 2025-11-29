from .types import Vote, Proposal, BlockHeader
from .constants import ConsensusStep

class MessageValidator:
    def __init__(self, chain_id: str):
        self.chain_id = chain_id


    def validate_vote(self, vote: Vote) -> bool:
        if vote.chain_id != self.chain_id:
            return False

        if vote.height < 0 or vote.round < 0:
            return False

        if vote.vote_type not in [ConsensusStep.PREVOTE, ConsensusStep.PRECOMMIT]:
            return False

        return True


    def validate_proposal(self, proposal: Proposal, block: BlockHeader) -> bool:
        if proposal.height != block.height:
            return False
        if proposal.block_id != block.block_id:
            return False

        return True


    def validate_block(self, block: BlockHeader) -> bool:
        if block.height < 0:
            return False
        return True
