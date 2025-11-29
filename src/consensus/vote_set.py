from collections import defaultdict
from typing import Dict, List
from .types import Vote
from .constants import ConsensusStep

class VoteSet:
    
    def __init__(self):
        self.votes: Dict[str, Dict[int, Dict[int, Dict[str, Vote]]]] = {
            ConsensusStep.PREVOTE: defaultdict(lambda: defaultdict(dict)),
            ConsensusStep.PRECOMMIT : defaultdict(lambda: defaultdict(dict))
        }

    def has_vote(self, vote: Vote) -> bool:
        return vote.validator in self.votes[vote.vote_type][vote.height][vote.round]

    def add_vote(self, vote: Vote) -> bool:
        if self.has_vote(vote):
            return False 

        self.votes[vote.vote_type][vote.height][vote.round][vote.validator] = vote
        return True

    def count_for_block(self, height: int, round: int, vote_type: str, block_id: str) -> int:
        return sum(1 for v in self.votes[vote_type][height][round].values()
                   if v.block_id == block_id)

    def get_votes(self, height: int, round: int, vote_type: str) -> List[Vote]:
        return list(self.votes[vote_type][height][round].values())