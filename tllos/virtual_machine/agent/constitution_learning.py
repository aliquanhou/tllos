#!/usr/bin/env python3
"""
TLL OS Constitution Learning

Agent proposes new rules from experience.
Human approval required before constitution update.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class RuleProposal:
    """A proposed new constitutional rule."""
    proposal_id: str
    name: str
    description: str
    source_experience: str  # experience_id that led to this proposal
    rationale: str
    status: str = "PENDING"  # PENDING / APPROVED / REJECTED
    proposed_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None


class TLLConstitutionLearning:
    """TLL OS Constitution Learning - learns rules from experience."""

    def __init__(self):
        self.proposals: List[RuleProposal] = []
        self.next_proposal_id = 0

    def propose_rule(self, name: str, description: str,
                     source_experience: str, rationale: str) -> RuleProposal:
        """Propose a new constitutional rule based on experience."""
        self.next_proposal_id += 1
        proposal = RuleProposal(
            proposal_id=f"rule-proposal-{self.next_proposal_id:04d}",
            name=name,
            description=description,
            source_experience=source_experience,
            rationale=rationale
        )
        self.proposals.append(proposal)
        return proposal

    def review_proposal(self, proposal_id: str, approved: bool,
                        reviewer: str = "human") -> Dict:
        """Human review of a rule proposal."""
        for proposal in self.proposals:
            if proposal.proposal_id == proposal_id:
                proposal.status = "APPROVED" if approved else "REJECTED"
                proposal.resolved_at = time.time()
                return {
                    "proposal_id": proposal_id,
                    "name": proposal.name,
                    "status": proposal.status,
                    "reviewer": reviewer
                }
        return {"error": "Proposal not found"}

    def get_pending_proposals(self) -> List[Dict]:
        """Get all pending proposals awaiting human review."""
        pending = [p for p in self.proposals if p.status == "PENDING"]
        return [
            {
                "id": p.proposal_id,
                "name": p.name,
                "description": p.description,
                "source": p.source_experience,
                "rationale": p.rationale
            }
            for p in pending
        ]

    def get_approved_rules(self) -> List[Dict]:
        """Get all approved rules."""
        approved = [p for p in self.proposals if p.status == "APPROVED"]
        return [
            {
                "id": p.proposal_id,
                "name": p.name,
                "description": p.description
            }
            for p in approved
        ]

    def learn_from_experience(self, experience) -> Optional[RuleProposal]:
        """Automatically propose a rule based on a failed experience."""
        if experience.result != "FAILED" or not experience.lesson:
            return None

        # Generate a rule proposal from the failure
        proposal_name = f"Rule: {experience.action} requires caution"
        description = f"Action '{experience.action}' led to failure: {experience.lesson}"
        rationale = f"Based on experience {experience.experience_id}: {experience.evidence}"

        return self.propose_rule(
            name=proposal_name,
            description=description,
            source_experience=experience.experience_id,
            rationale=rationale
        )

    def get_stats(self) -> Dict:
        """Get learning statistics."""
        pending = sum(1 for p in self.proposals if p.status == "PENDING")
        approved = sum(1 for p in self.proposals if p.status == "APPROVED")
        rejected = sum(1 for p in self.proposals if p.status == "REJECTED")
        return {
            "total_proposals": len(self.proposals),
            "pending": pending,
            "approved": approved,
            "rejected": rejected
        }
