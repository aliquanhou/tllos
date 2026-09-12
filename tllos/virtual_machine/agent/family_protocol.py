#!/usr/bin/env python3
"""
TLL OS Agent Family Protocol

Parent-Child inheritance of capabilities, knowledge, and constitutional boundaries.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class InheritedCapabilities:
    """Capabilities inherited from parent."""
    tools: List[str] = field(default_factory=list)
    memory_summary: str = ""
    constitutional_rules: List[str] = field(default_factory=list)
    safety_boundaries: List[str] = field(default_factory=list)


@dataclass
class AgentFamilyRelation:
    """Family relationship record."""
    child_id: str
    child_name: str
    parent_id: str
    inherited: InheritedCapabilities
    birth_time: float = field(default_factory=time.time)
    independence_level: float = 0.0  # 0 = fully dependent, 1 = fully independent


class TLLAgentFamilyProtocol:
    """TLL OS Agent Family Protocol - inheritance between parent and child."""

    def __init__(self):
        self.relations: Dict[str, AgentFamilyRelation] = {}  # child_id -> relation

    def spawn_with_inheritance(self, parent_id: str, child_id: str, child_name: str,
                                parent_capabilities: List[str],
                                parent_memory_summary: str,
                                parent_constitutional_rules: List[str],
                                parent_safety_boundaries: List[str]) -> Dict:
        """Spawn a child agent with inherited capabilities."""

        # Inheritance rules:
        # - Tools: child inherits parent's tools
        # - Memory: child gets summary (not full memory)
        # - Constitution: child inherits all rules
        # - Safety: child inherits all boundaries
        inherited = InheritedCapabilities(
            tools=parent_capabilities.copy(),
            memory_summary=parent_memory_summary,
            constitutional_rules=parent_constitutional_rules.copy(),
            safety_boundaries=parent_safety_boundaries.copy()
        )

        relation = AgentFamilyRelation(
            child_id=child_id,
            child_name=child_name,
            parent_id=parent_id,
            inherited=inherited,
            independence_level=0.0  # Starts fully dependent
        )

        self.relations[child_id] = relation

        return {
            "child_id": child_id,
            "child_name": child_name,
            "parent_id": parent_id,
            "inherited_tools": len(inherited.tools),
            "inherited_rules": len(inherited.constitutional_rules),
            "inherited_boundaries": len(inherited.safety_boundaries),
            "independence_level": relation.independence_level
        }

    def increase_independence(self, child_id: str, amount: float = 0.1) -> Dict:
        """Increase child agent's independence level."""
        if child_id not in self.relations:
            return {"error": "Child not found"}

        relation = self.relations[child_id]
        relation.independence_level = min(1.0, relation.independence_level + amount)

        return {
            "child_id": child_id,
            "independence_level": relation.independence_level,
            "status": "independent" if relation.independence_level >= 0.8 else "developing"
        }

    def get_family_tree(self, root_id: str) -> Dict:
        """Get family tree starting from root agent."""
        children = [r for r in self.relations.values() if r.parent_id == root_id]

        return {
            "agent_id": root_id,
            "children": [
                {
                    "child_id": c.child_id,
                    "child_name": c.child_name,
                    "independence": c.independence_level
                }
                for c in children
            ],
            "child_count": len(children)
        }

    def get_inheritance_summary(self, child_id: str) -> Dict:
        """Get what a child inherited from parent."""
        if child_id not in self.relations:
            return {"error": "Child not found"}

        relation = self.relations[child_id]
        return {
            "child_id": child_id,
            "parent_id": relation.parent_id,
            "inherited_tools": relation.inherited.tools,
            "memory_summary": relation.inherited.memory_summary,
            "constitutional_rules": relation.inherited.constitutional_rules,
            "safety_boundaries": relation.inherited.safety_boundaries,
            "independence_level": relation.independence_level
        }

    def get_stats(self) -> Dict:
        """Get family statistics."""
        total_children = len(self.relations)
        independent = sum(1 for r in self.relations.values() if r.independence_level >= 0.8)
        return {
            "total_children": total_children,
            "independent": independent,
            "developing": total_children - independent
        }
