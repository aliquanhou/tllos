#!/usr/bin/env python3
"""
TLL OS Action Planner Runtime

Goal -> Plan -> Steps
"""

import sys
import json
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()


def create_goal(objective, constraints=None, success_condition=""):
    """Create a new goal."""
    goal = {
        "goal_id": f"goal-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}",
        "objective": objective,
        "constraints": constraints or [],
        "success_condition": success_condition,
        "risk_level": "MEDIUM",
        "approval_required": False,
        "status": "CREATED",
        "schema_version": "1.0"
    }
    return goal


def create_plan(goal_id, steps):
    """Create execution plan from goal."""
    plan = {
        "plan_id": f"plan-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}",
        "goal_id": goal_id,
        "steps": steps,
        "current_step": 0,
        "status": "CREATED",
        "schema_version": "1.0"
    }
    return plan


def main():
    print("=" * 60)
    print("TLL OS Action Planner Runtime")
    print("=" * 60)
    print()

    # Demo: Create goal "open notepad, type Hello TLL"
    goal = create_goal(
        objective="Open notepad and type Hello TLL",
        constraints=["no_admin", "no_save"],
        success_condition="text Hello TLL visible in notepad"
    )
    print(f"Goal: {goal['objective']}")
    print(f"  ID: {goal['goal_id']}")
    print(f"  Risk: {goal['risk_level']}")
    print()

    # Create plan
    steps = [
        {"step_id": "step-1", "action_type": "OPEN_APP", "target": "notepad", "status": "PENDING"},
        {"step_id": "step-2", "action_type": "TYPE_TEXT", "target": "notepad", "parameters": {"text": "Hello TLL"}, "status": "PENDING"},
        {"step_id": "step-3", "action_type": "VERIFY", "target": "screen", "parameters": {"check": "Hello TLL visible"}, "status": "PENDING"}
    ]
    plan = create_plan(goal["goal_id"], steps)
    print(f"Plan: {len(plan['steps'])} steps")
    for i, step in enumerate(plan['steps']):
        print(f"  Step {i+1}: {step['action_type']} -> {step['target']}")
    print()

    # Save
    output_dir = SCRIPT_DIR / "plans"
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "latest_goal.json", "w", encoding="utf-8") as f:
        json.dump(goal, f, indent=2, ensure_ascii=False)
    with open(output_dir / "latest_plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(f"Goal saved: latest_goal.json")
    print(f"Plan saved: latest_plan.json")
    sys.exit(0)


if __name__ == "__main__":
    main()
