#!/usr/bin/env python3
"""
TLL OS Approval Gate

Human approval gate for agent actions.
No Evidence No Destruction.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TLLApprovalRequest:
    """Approval request from agent."""
    id: str
    action: str
    reason: str
    risk_level: str
    impact: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    status: str = "PENDING"  # PENDING, APPROVED, DENIED, MODIFIED


class TLLApprovalGate:
    """Manages approval requests."""

    def __init__(self):
        self.pending_requests: List[TLLApprovalRequest] = []
        self.history: List[TLLApprovalRequest] = []
        self._req_counter = 0
        self.auto_approve_low_risk = True

    def request_approval(self, action: str, reason: str,
                         risk_level: str, impact: List[str] = None,
                         evidence: List[str] = None) -> TLLApprovalRequest:
        """Request human approval for an action."""
        self._req_counter += 1
        req = TLLApprovalRequest(
            id=f"req_{self._req_counter:04d}",
            action=action,
            reason=reason,
            risk_level=risk_level,
            impact=impact or [],
            evidence=evidence or []
        )

        # Auto-approve low risk
        if self.auto_approve_low_risk and risk_level == "LOW":
            req.status = "APPROVED"
            self.history.append(req)
        else:
            self.pending_requests.append(req)

        return req

    def approve(self, request_id: str) -> Optional[TLLApprovalRequest]:
        """Approve a request."""
        for req in self.pending_requests:
            if req.id == request_id:
                req.status = "APPROVED"
                self.pending_requests.remove(req)
                self.history.append(req)
                return req
        return None

    def deny(self, request_id: str) -> Optional[TLLApprovalRequest]:
        """Deny a request."""
        for req in self.pending_requests:
            if req.id == request_id:
                req.status = "DENIED"
                self.pending_requests.remove(req)
                self.history.append(req)
                return req
        return None

    def get_pending(self) -> List[TLLApprovalRequest]:
        """Get pending requests."""
        return self.pending_requests

    def has_pending(self) -> bool:
        """Check if there are pending requests."""
        return len(self.pending_requests) > 0

    def get_status(self) -> Dict:
        """Get approval gate status."""
        return {
            "pending": len(self.pending_requests),
            "total_requests": self._req_counter,
            "auto_approve_low": self.auto_approve_low_risk
        }
