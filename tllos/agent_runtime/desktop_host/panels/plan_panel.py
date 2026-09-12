#!/usr/bin/env python3
"""
TLL OS Desktop Host - Plan Panel
"""

import json
from pathlib import Path


class PlanPanel:
    def __init__(self, planner_dir):
        self.planner_dir = Path(planner_dir)

    def get_status(self):
        plan_file = self.planner_dir / "plans" / "latest_plan.json"
        steps = []
        current_step = 0

        if plan_file.exists():
            with open(plan_file, 'r') as f:
                data = json.load(f)
            steps = [s.get("action_type", s.get("action", "")) for s in data.get("steps", [])]
            current_step = data.get("current_step", 0)

        return {
            "steps": steps,
            "current_step": current_step
        }

    def render(self):
        status = self.get_status()
        lines = [f"📋 PLAN"]
        for i, step in enumerate(status['steps']):
            marker = "→" if i == status['current_step'] else " "
            lines.append(f"  {marker} {i+1}. {step}")
        return "\n".join(lines)
