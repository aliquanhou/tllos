#!/usr/bin/env python3
"""
TLL OS Agent Live Loop

The core lifecycle of an autonomous agent:
  observe → understand → decide → risk_check → execute → remember
"""

import time
from typing import Dict, List, Optional

from .agent_self import TLLAgentSelf
from .world_model import TLLWorldModel
from .experience_memory import TLLExperienceMemory
from .tool_runtime import TLLToolRuntime
from .app_runtime import TLLAppRuntime
from .risk_evaluator import TLLActionRiskEvaluator


class TLLAgentLiveLoop:
    """Autonomous agent live loop."""

    def __init__(self,
                 agent_self: TLLAgentSelf,
                 world_model: TLLWorldModel,
                 experience: TLLExperienceMemory,
                 tool_runtime: TLLToolRuntime,
                 app_runtime: TLLAppRuntime,
                 risk_evaluator: TLLActionRiskEvaluator):
        self.agent_self = agent_self
        self.world_model = world_model
        self.experience = experience
        self.tool_runtime = tool_runtime
        self.app_runtime = app_runtime
        self.risk_evaluator = risk_evaluator

        # Loop state
        self.running = False
        self.current_goal = ""
        self.current_plan: List[str] = []
        self.current_step = 0
        self.current_thinking = ""
        self.current_action = ""
        self.waiting_approval = False
        self.approval_decision = None
        self.last_result = ""
        self.loop_count = 0

    def observe(self) -> Dict:
        """Observe the current world state."""
        self.current_thinking = "Observing world..."
        world_summary = self.world_model.get_world_summary()
        health = self.agent_self.get_health_summary()
        return {
            "world_objects": world_summary["total_objects"],
            "agent_state": health["survival"],
            "energy": health["energy"]
        }

    def understand(self, goal: str) -> Dict:
        """Understand the goal."""
        self.current_thinking = f"Understanding: {goal[:30]}"
        self.current_goal = goal

        # Analyze what's needed
        needs = []
        if "商城" in goal or "mall" in goal.lower():
            needs = ["database", "backend", "frontend"]
        elif "应用" in goal or "app" in goal.lower():
            needs = ["project", "code", "build"]
        else:
            needs = ["analyze", "plan", "execute"]

        return {"goal": goal, "needs": needs}

    def decide(self, understanding: Dict) -> Dict:
        """Decide on a plan."""
        self.current_thinking = "Planning..."
        needs = understanding.get("needs", [])

        plan = []
        for need in needs:
            plan.append(f"Create {need}")
        plan.append("Verify result")

        self.current_plan = plan
        self.current_step = 0

        return {"plan": plan}

    def risk_check(self, action: str) -> Dict:
        """Check risk of action."""
        evaluation = self.risk_evaluator.evaluate_action(action, params=None, world_model=self.world_model)
        return {
            "action": action,
            "risk_level": evaluation.risk_level,
            "approved": evaluation.risk_level in ["LOW", "MEDIUM"],
            "requires_approval": evaluation.requires_approval
        }

    def execute(self, step: str) -> Dict:
        """Execute a step."""
        self.current_action = step
        self.current_thinking = f"Executing: {step[:30]}"
        self.waiting_approval = False

        # Risk check
        risk = self.risk_check(step)
        if not risk["approved"]:
            self.waiting_approval = True
            return {
                "step": step,
                "status": "WAIT_APPROVAL",
                "risk": risk["risk_level"]
            }

        # Actually "execute" (mock but structured)
        time.sleep(0.1)
        self.current_step += 1
        self.last_result = f"Done: {step[:30]}"

        return {
            "step": step,
            "status": "EXECUTED",
            "risk": risk["risk_level"]
        }

    def remember(self, action: str, result: str, risk: str):
        """Remember the experience."""
        self.experience.record_experience(
            action=action,
            evidence=f"executed_{self.loop_count}",
            world_before={},
            world_after={},
            result=result,
            lesson=f"Step completed: {action[:30]}",
            risk_level=risk
        )

    def run_cycle(self, goal: str = None) -> Dict:
        """Run one complete agent cycle."""
        self.loop_count += 1

        # 1. Observe
        observation = self.observe()

        # 2. Understand
        if goal:
            understanding = self.understand(goal)
        else:
            understanding = {"goal": self.current_goal, "needs": []}

        # 3. Decide
        decision = self.decide(understanding)

        # 4. Execute first step
        if self.current_plan:
            result = self.execute(self.current_plan[0])

            # 5. Remember
            self.remember(
                action=self.current_plan[0],
                result=result["status"],
                risk=result.get("risk", "LOW")
            )

        self.current_thinking = "Cycle complete, awaiting next goal"
        return {
            "loop": self.loop_count,
            "goal": self.current_goal,
            "plan": self.current_plan,
            "step": self.current_step,
            "result": self.last_result
        }

    def request_approval(self) -> bool:
        """Request human approval for current action."""
        self.waiting_approval = True
        self.current_thinking = "等待主人批准..."
        # In real system, this would block for human input
        # For now, return True (auto-approve for demo)
        return True

    def approve(self):
        """Human approves current action."""
        self.approval_decision = "APPROVED"
        self.waiting_approval = False
        self.current_thinking = "已批准，继续执行..."

    def deny(self):
        """Human denies current action."""
        self.approval_decision = "DENIED"
        self.waiting_approval = False
        self.current_thinking = "已拒绝，等待新指令..."

    def get_status(self) -> Dict:
        """Get current agent status."""
        return {
            "running": self.running,
            "goal": self.current_goal,
            "thinking": self.current_thinking,
            "plan": self.current_plan,
            "step": self.current_step,
            "action": self.current_action,
            "waiting_approval": self.waiting_approval,
            "result": self.last_result,
            "loop_count": self.loop_count
        }
