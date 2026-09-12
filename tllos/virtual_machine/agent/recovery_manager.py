#!/usr/bin/env python3
"""
TLL OS Recovery Capability

Checkpoint, restore, and rollback for Agent safety.
"""

import time
import copy
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Checkpoint:
    """System checkpoint."""
    checkpoint_id: str
    description: str
    timestamp: float = field(default_factory=time.time)
    state_snapshot: Dict = field(default_factory=dict)


class TLLRecoveryManager:
    """TLL OS Recovery Manager."""

    def __init__(self):
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.rollback_count = 0

    def create_checkpoint(self, description: str, state_snapshot: Dict = None) -> Checkpoint:
        """Create a system checkpoint."""
        checkpoint_id = f"ckpt-{len(self.checkpoints) + 1:04d}"
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            description=description,
            state_snapshot=copy.deepcopy(state_snapshot or {})
        )
        self.checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    def restore_checkpoint(self, checkpoint_id: str) -> Dict:
        """Restore to a checkpoint."""
        if checkpoint_id not in self.checkpoints:
            return {
                "success": False,
                "error": f"Checkpoint not found: {checkpoint_id}"
            }

        checkpoint = self.checkpoints[checkpoint_id]
        self.rollback_count += 1

        return {
            "success": True,
            "checkpoint_id": checkpoint_id,
            "description": checkpoint.description,
            "timestamp": checkpoint.timestamp,
            "state_snapshot": checkpoint.state_snapshot,
            "message": f"Restored to checkpoint: {checkpoint_id}"
        }

    def list_checkpoints(self) -> Dict:
        """List all checkpoints."""
        checkpoints = []
        for cid, ckpt in self.checkpoints.items():
            checkpoints.append({
                "id": ckpt.checkpoint_id,
                "description": ckpt.description,
                "timestamp": ckpt.timestamp
            })

        return {
            "checkpoints": checkpoints,
            "count": len(checkpoints)
        }

    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """Get the most recent checkpoint."""
        if not self.checkpoints:
            return None
        latest_id = max(self.checkpoints.keys(),
                        key=lambda k: self.checkpoints[k].timestamp)
        return self.checkpoints[latest_id]

    def rollback_to_latest(self) -> Dict:
        """Rollback to the latest checkpoint."""
        latest = self.get_latest_checkpoint()
        if not latest:
            return {"success": False, "error": "No checkpoints available"}

        return self.restore_checkpoint(latest.checkpoint_id)

    def get_stats(self) -> Dict:
        """Get recovery statistics."""
        return {
            "total_checkpoints": len(self.checkpoints),
            "total_rollbacks": self.rollback_count
        }
