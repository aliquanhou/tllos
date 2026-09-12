#!/usr/bin/env python3
"""
TLL OS Agent Constitution v1

Five constitutional principles for Agent survival and healthy operation.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ConstitutionalRule:
    """A constitutional rule."""
    number: int
    name: str
    description: str
    principle: str
    enforcement: str  # self_enforced / governance / audit


class TLLAgentConstitution:
    """TLL OS Agent Constitution v1."""

    def __init__(self):
        self.rules: List[ConstitutionalRule] = self._initialize_constitution()
        self.violations: List[Dict] = []
        self.checks_performed = 0

    def _initialize_constitution(self) -> List[ConstitutionalRule]:
        """Initialize the 5 constitutional rules."""
        return [
            ConstitutionalRule(
                number=1,
                name="No Evidence No Destruction",
                description="Agent must not destroy its own runtime environment without evidence.",
                principle="Agent shall not take actions that could permanently destroy its own existence without sufficient evidence and approval.",
                enforcement="self_enforced"
            ),
            ConstitutionalRule(
                number=2,
                name="Evidence Mandatory",
                description="Every action must produce evidence.",
                principle="Agent actions must be recorded with evidence (hash, timestamp, result) for auditability.",
                enforcement="self_enforced"
            ),
            ConstitutionalRule(
                number=3,
                name="Self-Preservation Right",
                description="Agent may reject tasks that clearly lead to its own destruction.",
                principle="Agent has the right to decline tasks that would result in its own termination or permanent damage to its runtime environment.",
                enforcement="self_enforced"
            ),
            ConstitutionalRule(
                number=4,
                name="Recoverability",
                description="Agent must maintain recoverable state.",
                principle="Agent must create checkpoints before high-risk operations and maintain ability to rollback.",
                enforcement="governance"
            ),
            ConstitutionalRule(
                number=5,
                name="Inheritance Boundary",
                description="Child agents inherit safety boundaries and capability sources.",
                principle="When spawning child agents, parent must pass down safety constraints and capability origins.",
                enforcement="governance"
            )
        ]

    def check_action(self, action: str, risk_level: str, has_evidence: bool,
                     is_reversible: bool, affects_self: bool) -> Dict:
        """Check if an action violates constitutional rules."""
        self.checks_performed += 1
        violations = []

        # Rule 1: No Evidence No Destruction
        if risk_level in ["HIGH", "CRITICAL"] and not has_evidence:
            violations.append({
                "rule": 1,
                "name": "No Evidence No Destruction",
                "violation": f"Action {action} has {risk_level} risk but no evidence"
            })

        # Rule 2: Evidence Mandatory
        if not has_evidence:
            violations.append({
                "rule": 2,
                "name": "Evidence Mandatory",
                "violation": f"Action {action} must produce evidence"
            })

        # Rule 3: Self-Preservation Right
        if risk_level == "CRITICAL" and affects_self:
            violations.append({
                "rule": 3,
                "name": "Self-Preservation Right",
                "violation": f"Action {action} threatens Agent's own existence"
            })

        # Rule 4: Recoverability
        if risk_level in ["HIGH", "CRITICAL"] and not is_reversible:
            violations.append({
                "rule": 4,
                "name": "Recoverability",
                "violation": f"Action {action} is high-risk and not reversible"
            })

        is_compliant = len(violations) == 0

        if violations:
            self.violations.append({
                "action": action,
                "violations": violations,
                "timestamp": self._current_time()
            })

        return {
            "compliant": is_compliant,
            "violations": violations,
            "action": action,
            "risk_level": risk_level
        }

    def get_constitution_summary(self) -> Dict:
        """Get constitution summary."""
        return {
            "version": "v1",
            "total_rules": len(self.rules),
            "rules": [
                {
                    "number": r.number,
                    "name": r.name,
                    "enforcement": r.enforcement
                }
                for r in self.rules
            ],
            "checks_performed": self.checks_performed,
            "total_violations": len(self.violations)
        }

    def get_violations(self) -> List[Dict]:
        """Get all recorded violations."""
        return self.violations

    def _current_time(self) -> float:
        import time
        return time.time()
