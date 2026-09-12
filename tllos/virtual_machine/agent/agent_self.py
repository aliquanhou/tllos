#!/usr/bin/env python3
"""
TLL OS Agent Self State

Agent's self-awareness and constitutional state.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class AgentSelfState:
    """Agent self-state - constitutional awareness."""
    identity: str = "tll-agent-0"
    version: str = "0.1.0"
    birth_time: float = field(default_factory=time.time)

    # Capability
    tool_count: int = 0
    filesystem_files: int = 0
    process_count: int = 0
    app_count: int = 0

    # Health
    energy: float = 100.0  # 0-100
    memory_health: str = "HEALTHY"  # HEALTHY / DEGRADED / CRITICAL
    risk_level: str = "LOW"  # LOW / MEDIUM / HIGH / CRITICAL

    # Survival
    survival_status: str = "ALIVE"  # ALIVE / WOUNDED / DYING / DEAD
    recovery_count: int = 0
    error_count: int = 0

    # Relationships
    parent_agent: Optional[str] = None
    child_agents: List[str] = field(default_factory=list)

    # Checkpoints
    checkpoints: List[Dict] = field(default_factory=list)


class TLLAgentSelf:
    """TLL OS Agent Self State Manager."""

    def __init__(self, agent_id: str = "tll-agent-0"):
        self.state = AgentSelfState(identity=agent_id)

    def update_capability(self, tool_count: int = 0, filesystem_files: int = 0,
                          process_count: int = 0, app_count: int = 0):
        """Update capability metrics."""
        self.state.tool_count = tool_count
        self.state.filesystem_files = filesystem_files
        self.state.process_count = process_count
        self.state.app_count = app_count

    def update_health(self, energy: float = None, memory_health: str = None,
                      risk_level: str = None):
        """Update health metrics."""
        if energy is not None:
            self.state.energy = max(0.0, min(100.0, energy))
        if memory_health is not None:
            self.state.memory_health = memory_health
        if risk_level is not None:
            self.state.risk_level = risk_level

    def record_error(self):
        """Record an error."""
        self.state.error_count += 1
        self.state.energy = max(0.0, self.state.energy - 5.0)

        if self.state.energy < 20:
            self.state.survival_status = "DYING"
        elif self.state.energy < 50:
            self.state.survival_status = "WOUNDED"

    def record_recovery(self):
        """Record a recovery."""
        self.state.recovery_count += 1
        self.state.energy = min(100.0, self.state.energy + 10.0)

        if self.state.energy > 50:
            self.state.survival_status = "ALIVE"

    def add_child(self, child_id: str):
        """Add child agent."""
        if child_id not in self.state.child_agents:
            self.state.child_agents.append(child_id)

    def set_parent(self, parent_id: str):
        """Set parent agent."""
        self.state.parent_agent = parent_id

    def add_checkpoint(self, checkpoint_id: str, description: str):
        """Add a checkpoint."""
        self.state.checkpoints.append({
            "id": checkpoint_id,
            "description": description,
            "timestamp": time.time()
        })

    def get_self_state(self) -> Dict:
        """Get full self state."""
        return asdict(self.state)

    def get_health_summary(self) -> Dict:
        """Get health summary."""
        return {
            "identity": self.state.identity,
            "energy": self.state.energy,
            "survival": self.state.survival_status,
            "risk": self.state.risk_level,
            "memory_health": self.state.memory_health,
            "errors": self.state.error_count,
            "recoveries": self.state.recovery_count
        }
