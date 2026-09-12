#!/usr/bin/env python3
"""
TLL OS Agent Spawn Protocol

Parent-Child Agent relationships.
"""

import time
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class AgentRecord:
    """Record of an Agent."""
    agent_id: str
    name: str
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    birth_time: float = field(default_factory=time.time)
    status: str = "ACTIVE"  # ACTIVE / TERMINATED
    capabilities: List[str] = field(default_factory=list)


class TLLAgentSpawner:
    """TLL OS Agent Spawn Protocol."""

    def __init__(self):
        self.agents: Dict[str, AgentRecord] = {}
        self.next_agent_num = 0

    def spawn_agent(self, parent_id: str, name: str = None,
                    capabilities: List[str] = None) -> Dict:
        """Spawn a child agent."""
        self.next_agent_num += 1
        agent_id = f"tll-agent-{self.next_agent_num}"
        agent_name = name or f"Agent-{self.next_agent_num}"

        # Create child record
        child = AgentRecord(
            agent_id=agent_id,
            name=agent_name,
            parent_id=parent_id,
            capabilities=capabilities or []
        )
        self.agents[agent_id] = child

        # Update parent
        if parent_id in self.agents:
            self.agents[parent_id].child_ids.append(agent_id)

        return {
            "agent_id": agent_id,
            "name": agent_name,
            "parent_id": parent_id,
            "capabilities": child.capabilities,
            "status": child.status,
            "birth_time": child.birth_time
        }

    def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    def get_children(self, agent_id: str) -> List[Dict]:
        """Get all children of an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return []

        children = []
        for child_id in agent.child_ids:
            child = self.agents.get(child_id)
            if child:
                children.append({
                    "agent_id": child.agent_id,
                    "name": child.name,
                    "status": child.status
                })
        return children

    def get_hierarchy(self) -> Dict:
        """Get full agent hierarchy."""
        roots = [a for a in self.agents.values() if a.parent_id is None]

        def build_tree(agent: AgentRecord) -> Dict:
            return {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "status": agent.status,
                "children": [build_tree(self.agents[cid]) for cid in agent.child_ids
                             if cid in self.agents]
            }

        return {
            "roots": [build_tree(r) for r in roots],
            "total_agents": len(self.agents)
        }

    def terminate_agent(self, agent_id: str) -> Dict:
        """Terminate an agent."""
        if agent_id not in self.agents:
            return {"success": False, "error": "Agent not found"}

        agent = self.agents[agent_id]
        agent.status = "TERMINATED"

        return {
            "success": True,
            "agent_id": agent_id,
            "name": agent.name,
            "status": agent.status
        }

    def get_stats(self) -> Dict:
        """Get spawn statistics."""
        active = sum(1 for a in self.agents.values() if a.status == "ACTIVE")
        terminated = sum(1 for a in self.agents.values() if a.status == "TERMINATED")
        return {
            "total_agents": len(self.agents),
            "active": active,
            "terminated": terminated
        }
