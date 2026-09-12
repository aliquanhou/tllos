#!/usr/bin/env python3
"""
TLL OS Experience Memory

Rich experience records with lessons learned.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Experience:
    """A rich experience record."""
    experience_id: str
    action: str
    evidence: str = ""
    world_before: Dict = field(default_factory=dict)
    world_after: Dict = field(default_factory=dict)
    result: str = ""  # SUCCESS / FAILED
    lesson: str = ""
    risk_level: str = "LOW"
    timestamp: float = field(default_factory=time.time)


class TLLExperienceMemory:
    """TLL OS Experience Memory - learns from actions."""

    def __init__(self):
        self.experiences: List[Experience] = []
        self.next_id = 0

    def record_experience(self, action: str, evidence: str,
                          world_before: Dict, world_after: Dict,
                          result: str, lesson: str = "",
                          risk_level: str = "LOW") -> Experience:
        """Record a rich experience."""
        self.next_id += 1
        exp = Experience(
            experience_id=f"exp-{self.next_id:04d}",
            action=action,
            evidence=evidence,
            world_before=world_before,
            world_after=world_after,
            result=result,
            lesson=lesson,
            risk_level=risk_level
        )
        self.experiences.append(exp)
        return exp

    def recall_similar(self, action: str, limit: int = 5) -> List[Dict]:
        """Recall experiences similar to this action."""
        similar = [e for e in self.experiences if action.lower() in e.action.lower()]
        return [
            {
                "id": e.experience_id,
                "action": e.action,
                "result": e.result,
                "lesson": e.lesson,
                "risk": e.risk_level
            }
            for e in similar[-limit:]
        ]

    def get_failure_patterns(self) -> List[Dict]:
        """Extract failure patterns from experiences."""
        failures = [e for e in self.experiences if e.result == "FAILED"]
        patterns = []
        for f in failures:
            patterns.append({
                "action": f.action,
                "lesson": f.lesson,
                "risk": f.risk_level,
                "evidence": f.evidence
            })
        return patterns

    def get_success_patterns(self) -> List[Dict]:
        """Extract success patterns from experiences."""
        successes = [e for e in self.experiences if e.result == "SUCCESS"]
        patterns = []
        for s in successes:
            patterns.append({
                "action": s.action,
                "lesson": s.lesson,
                "risk": s.risk_level
            })
        return patterns

    def get_lessons(self, action_type: str = None) -> List[str]:
        """Get lessons learned, optionally filtered by action type."""
        lessons = []
        for e in self.experiences:
            if e.lesson and (action_type is None or action_type.lower() in e.action.lower()):
                lessons.append(e.lesson)
        return lessons

    def get_stats(self) -> Dict:
        """Get experience statistics."""
        successes = sum(1 for e in self.experiences if e.result == "SUCCESS")
        failures = sum(1 for e in self.experiences if e.result == "FAILED")
        return {
            "total_experiences": len(self.experiences),
            "successes": successes,
            "failures": failures,
            "lessons_learned": sum(1 for e in self.experiences if e.lesson)
        }
