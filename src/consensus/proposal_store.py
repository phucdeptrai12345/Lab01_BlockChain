from collections import defaultdict
from .types import Proposal


class ProposalStore:

    def __init__(self):
        self.proposals = defaultdict(dict)

    def save(self, proposal: Proposal):
        self.proposals[proposal.height][proposal.round] = proposal

    def get(self, height: int, round: int):
        return self.proposals.get(height, {}).get(round)

    def has(self, height: int, round: int):
        return round in self.proposals.get(height, {})
