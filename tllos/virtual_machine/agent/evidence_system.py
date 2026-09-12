#!/usr/bin/env python3
"""
TLL OS Agent Evidence System

Every action produces evidence:
  Action + Reason + Risk + Permission + Result + Hash
"""

import time
import hashlib
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class TLLActionEvidence:
    """Evidence for one action."""
    id: str
    action: str
    reason: str
    risk_level: str
    approved: bool
    result: str
    evidence_hash: str
    timestamp: float = field(default_factory=time.time)


class TLLEvidenceSystem:
    """Manages action evidence."""

    def __init__(self):
        self.records: List[TLLActionEvidence] = []
        self._counter = 0

    def record(self, action: str, reason: str, risk_level: str,
               approved: bool, result: str) -> TLLActionEvidence:
        """Record evidence for an action."""
        self._counter += 1

        # Compute evidence hash
        evidence_data = json.dumps({
            "action": action,
            "reason": reason,
            "risk": risk_level,
            "approved": approved,
            "result": result,
            "timestamp": time.time()
        }, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_data.encode()).hexdigest()[:16]

        record = TLLActionEvidence(
            id=f"evd_{self._counter:04d}",
            action=action,
            reason=reason,
            risk_level=risk_level,
            approved=approved,
            result=result,
            evidence_hash=evidence_hash
        )
        self.records.append(record)
        return record

    def get_recent(self, limit: int = 10) -> List[TLLActionEvidence]:
        """Get recent evidence records."""
        return self.records[-limit:]

    def get_stats(self) -> Dict:
        """Get evidence stats."""
        return {
            "total_records": len(self.records),
            "approved_count": sum(1 for r in self.records if r.approved),
            "success_count": sum(1 for r in self.records if r.result == "success")
        }

    def get_status(self) -> Dict:
        """Get evidence system status."""
        return {
            "total": len(self.records),
            "last_hash": self.records[-1].evidence_hash if self.records else "---"
        }
