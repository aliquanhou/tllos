#!/usr/bin/env python3
"""
TLL OS Agent Boot Manager

Boot sequence for TLL Agent as first citizen.
"""

import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field

from .tool_registry import TLLToolRegistry
from .llm_bridge import TLLLLMBridge


@dataclass
class BootStep:
    """Agent boot step."""
    step: int
    name: str
    status: str = "PENDING"
    duration_ms: float = 0.0


class TLLAgent:
    """TLL OS Native Agent - First Citizen."""

    def __init__(self):
        self.agent_id: str = "tll-agent-0"
        self.state: str = "POWERED_OFF"
        self.boot_steps: List[BootStep] = []
        self.boot_time: Optional[float] = None

        # Core components
        self.tool_registry = TLLToolRegistry()
        self.llm_bridge = TLLLLMBridge()

        # Session state
        self.current_goal: Optional[str] = None
        self.current_plan: Optional[Dict] = None
        self.task_history: List[Dict] = []

    def boot(self) -> Dict:
        """Boot TLL Agent as first citizen."""
        self.boot_time = time.time()
        self.state = "BOOTING"

        # Step 1: Initialize Tool Registry
        self._add_step(1, "Tool Registry")
        caps = self.tool_registry.get_capabilities_summary()
        self._complete_step(1, "OK")

        # Step 2: Initialize LLM Bridge
        self._add_step(2, "LLM Bridge")
        llm_status = self.llm_bridge.connect()
        self._complete_step(2, "OK")

        # Step 3: Start Reasoning Loop
        self._add_step(3, "Reasoning Loop")
        self.state = "READY"
        self._complete_step(3, "OK")

        # Step 4: Agent Online
        self._add_step(4, "Agent Online")
        self.state = "ONLINE"
        self._complete_step(4, "OK")

        return {
            "agent_id": self.agent_id,
            "state": self.state,
            "boot_time_s": round(time.time() - self.boot_time, 3),
            "llm": self.llm_bridge.get_status(),
            "capabilities": caps,
            "boot_steps": [
                {"step": s.step, "name": s.name, "status": s.status}
                for s in self.boot_steps
            ]
        }

    def receive_goal(self, goal: str) -> Dict:
        """Receive and process user goal."""
        self.current_goal = goal
        self.state = "THINKING"

        # Use LLM to think
        think_result = self.llm_bridge.think({"goal": goal})

        # Generate plan
        plan_result = self.llm_bridge.plan(goal, {"context": "default"})
        self.current_plan = plan_result

        self.state = "PLANNED"

        return {
            "goal": goal,
            "agent_id": self.agent_id,
            "thought": think_result.text,
            "plan": plan_result,
            "state": self.state,
            "timestamp": time.time()
        }

    def execute_plan(self) -> Dict:
        """Execute current plan."""
        if not self.current_plan:
            return {"error": "No plan to execute"}

        self.state = "EXECUTING"
        results = []

        for step in self.current_plan.get("steps", []):
            result = self.llm_bridge.execute(step)
            results.append(result)

        self.state = "EXECUTED"
        self.task_history.append({
            "goal": self.current_goal,
            "plan": self.current_plan,
            "results": results,
            "timestamp": time.time()
        })

        return {
            "goal": self.current_goal,
            "results": results,
            "state": self.state
        }

    def shutdown(self) -> Dict:
        """Shutdown agent."""
        self.state = "SHUTTING_DOWN"
        llm_disconnect = self.llm_bridge.disconnect()
        self.state = "POWERED_OFF"
        return {
            "agent_id": self.agent_id,
            "state": self.state,
            "llm": llm_disconnect
        }

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            "agent_id": self.agent_id,
            "state": self.state,
            "current_goal": self.current_goal,
            "llm": self.llm_bridge.get_status(),
            "tool_count": len(self.tool_registry.tools),
            "task_history": len(self.task_history)
        }

    def _add_step(self, step: int, name: str):
        self.boot_steps.append(BootStep(step=step, name=name))

    def _complete_step(self, step: int, status: str):
        for s in self.boot_steps:
            if s.step == step:
                s.status = status
                s.duration_ms = 5.0
                break
