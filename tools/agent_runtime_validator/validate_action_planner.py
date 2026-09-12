#!/usr/bin/env python3
"""
TLL OS Action Planner Validator

Gates:
- Gate 1: Goal Schema
- Gate 2: Plan Schema
- Gate 3: Grounding Schema
- Gate 4: Feedback Loop
- Gate 5: Recovery Model
"""

import json
import sys
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent


def validate_json_file(file_path):
    full_path = os.path.join(PROJECT_ROOT, file_path)
    if not os.path.exists(full_path):
        return False, f"File not found: {file_path}"
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Parse error: {e}"
    return True, data


def main():
    print("=" * 60)
    print("TLL OS Action Planner Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Goal Schema
    print("--- Gate 1: Goal Schema ---")
    ok, schema = validate_json_file("tllos/agent_runtime/action_planner/goal_model.json")
    if not ok:
        print(f"  >> FAIL: {schema}")
        all_passed = False
        results.append(("Gate 1: Goal Schema", "FAIL"))
    else:
        required = ["goal_id", "objective", "constraints", "success_condition", "risk_level"]
        missing = [f for f in required if f not in schema]
        if missing:
            print(f"  >> FAIL: missing: {missing}")
            all_passed = False
            results.append(("Gate 1: Goal Schema", "FAIL"))
        else:
            print(f"  >> PASS: goal schema valid")
            results.append(("Gate 1: Goal Schema", "PASS"))

    # Gate 2: Plan Schema
    print()
    print("--- Gate 2: Plan Schema ---")
    ok, plan = validate_json_file("tllos/agent_runtime/action_planner/task_plan.json")
    if not ok:
        print(f"  >> FAIL: {plan}")
        all_passed = False
        results.append(("Gate 2: Plan Schema", "FAIL"))
    else:
        required = ["plan_id", "goal_id", "steps", "current_step", "status"]
        missing = [f for f in required if f not in plan]
        if missing:
            print(f"  >> FAIL: missing: {missing}")
            all_passed = False
            results.append(("Gate 2: Plan Schema", "FAIL"))
        else:
            print(f"  >> PASS: plan schema valid")
            results.append(("Gate 2: Plan Schema", "PASS"))

    # Gate 3: Grounding Schema
    print()
    print("--- Gate 3: Grounding Schema ---")
    ok, grounding = validate_json_file("tllos/agent_runtime/action_planner/object_grounding.json")
    if not ok:
        print(f"  >> FAIL: {grounding}")
        all_passed = False
        results.append(("Gate 3: Grounding Schema", "FAIL"))
    else:
        required = ["grounding_id", "target_description", "matched_objects", "confidence_threshold"]
        missing = [f for f in required if f not in grounding]
        if missing:
            print(f"  >> FAIL: missing: {missing}")
            all_passed = False
            results.append(("Gate 3: Grounding Schema", "FAIL"))
        else:
            print(f"  >> PASS: grounding schema valid")
            results.append(("Gate 3: Grounding Schema", "PASS"))

    # Gate 4: Feedback Loop
    print()
    print("--- Gate 4: Feedback Loop ---")
    fb_path = os.path.join(PROJECT_ROOT, "tllos/agent_runtime/action_planner/feedback_loop.md")
    if os.path.exists(fb_path):
        print(f"  >> PASS: feedback loop documented")
        results.append(("Gate 4: Feedback Loop", "PASS"))
    else:
        print(f"  >> FAIL: feedback loop missing")
        all_passed = False
        results.append(("Gate 4: Feedback Loop", "FAIL"))

    # Gate 5: Recovery Model
    print()
    print("--- Gate 5: Recovery Model ---")
    rec_path = os.path.join(PROJECT_ROOT, "tllos/agent_runtime/action_planner/recovery_model.md")
    if os.path.exists(rec_path):
        print(f"  >> PASS: recovery model documented")
        results.append(("Gate 5: Recovery Model", "PASS"))
    else:
        print(f"  >> FAIL: recovery model missing")
        all_passed = False
        results.append(("Gate 5: Recovery Model", "FAIL"))

    print()
    print("=" * 60)
    if all_passed:
        print("Action Planner Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        sys.exit(0)
    else:
        print("Action Planner Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        sys.exit(1)


if __name__ == "__main__":
    main()
