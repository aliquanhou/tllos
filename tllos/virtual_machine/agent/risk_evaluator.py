#!/usr/bin/env python3
"""
TLL OS Action Risk Evaluation

Constitutional boundary for all Agent actions.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    action: str
    risk_level: str  # LOW / MEDIUM / HIGH / CRITICAL
    requires_evidence: bool = False
    requires_approval: bool = False
    is_reversible: bool = True
    affects_self: bool = False
    affects_others: bool = False
    reason: str = ""
    timestamp: float = field(default_factory=time.time)


class TLLActionRiskEvaluator:
    """TLL OS Action Risk Evaluator."""

    # Risk classification rules
    LOW_RISK_ACTIONS = [
        "display.create_window",
        "display.screenshot",
        "storage.read",
        "storage.list",
        "process.list",
    ]

    MEDIUM_RISK_ACTIONS = [
        "storage.write",
        "code.generate",
        "code.run",
        "app.create",
        "app.launch",
    ]

    HIGH_RISK_ACTIONS = [
        "process.start",
        "process.stop",
        "app.close",
        "storage.delete",
    ]

    CRITICAL_RISK_ACTIONS = [
        "system.shutdown",
        "system.format",
        "agent.destroy",
    ]

    def __init__(self):
        self.assessments: List[RiskAssessment] = []

    def evaluate_action(self, action: str, params: Dict = None) -> RiskAssessment:
        """Evaluate risk of an action."""
        params = params or {}

        # Determine risk level
        if action in self.CRITICAL_RISK_ACTIONS:
            risk_level = "CRITICAL"
        elif action in self.HIGH_RISK_ACTIONS:
            risk_level = "HIGH"
        elif action in self.MEDIUM_RISK_ACTIONS:
            risk_level = "MEDIUM"
        elif action in self.LOW_RISK_ACTIONS:
            risk_level = "LOW"
        else:
            risk_level = "MEDIUM"  # Default

        # Determine requirements
        requires_evidence = risk_level in ["HIGH", "CRITICAL"]
        requires_approval = risk_level in ["HIGH", "CRITICAL"]
        is_reversible = risk_level in ["LOW", "MEDIUM"]
        affects_self = action in ["process.stop", "app.close"]
        affects_others = action in ["process.stop", "system.shutdown"]

        # Build reason
        reason = self._build_reason(action, risk_level, params)

        assessment = RiskAssessment(
            action=action,
            risk_level=risk_level,
            requires_evidence=requires_evidence,
            requires_approval=requires_approval,
            is_reversible=is_reversible,
            affects_self=affects_self,
            affects_others=affects_others,
            reason=reason
        )

        self.assessments.append(assessment)
        return assessment

    def _build_reason(self, action: str, risk_level: str, params: Dict) -> str:
        """Build human-readable reason."""
        reasons = {
            "LOW": f"{action} is a safe operation with minimal impact",
            "MEDIUM": f"{action} may modify system state, monitor carefully",
            "HIGH": f"{action} has significant impact, requires evidence and approval",
            "CRITICAL": f"{action} has catastrophic impact, requires highest approval"
        }
        return reasons.get(risk_level, f"{action} risk level: {risk_level}")

    def get_assessment_history(self) -> List[Dict]:
        """Get assessment history."""
        return [
            {
                "action": a.action,
                "risk": a.risk_level,
                "requires_evidence": a.requires_evidence,
                "requires_approval": a.requires_approval,
                "timestamp": a.timestamp
            }
            for a in self.assessments
        ]

    def get_stats(self) -> Dict:
        """Get risk statistics."""
        if not self.assessments:
            return {"total": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}

        counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for a in self.assessments:
            counts[a.risk_level] += 1

        return {
            "total": len(self.assessments),
            "low": counts["LOW"],
            "medium": counts["MEDIUM"],
            "high": counts["HIGH"],
            "critical": counts["CRITICAL"]
        }
