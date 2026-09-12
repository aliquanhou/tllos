#!/usr/bin/env python3
"""
TLL OS Agent Reasoning Runtime

Goal -> Reasoning -> Decision -> Plan
"""

import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()


def compute_hash(data):
    """Compute SHA256 hash of data."""
    h = hashlib.sha256()
    h.update(json.dumps(data, sort_keys=True).encode())
    return h.hexdigest()


def reason(goal, context=None, constraints=None):
    """
    Reason about a goal.
    Returns reasoning decision with confidence.
    """
    reasoning_id = f"reason-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
    context = context or {}
    constraints = constraints or []

    # Goal decomposition (rule-based, not LLM)
    if "open" in goal.lower():
        options = [
            {"action": "OPEN_APP", "target": goal.lower().replace("open ", ""), "confidence": 0.85},
            {"action": "SEARCH", "target": goal, "confidence": 0.6}
        ]
        decision = options[0]  # Choose highest confidence
    elif "click" in goal.lower():
        options = [
            {"action": "MOVE_MOUSE", "target": "identified_object", "confidence": 0.75},
            {"action": "CLICK", "target": "identified_object", "confidence": 0.8}
        ]
        decision = options[1]
    else:
        options = [
            {"action": "OBSERVE", "target": "screen", "confidence": 0.9}
        ]
        decision = options[0]

    reasoning = {
        "reasoning_id": reasoning_id,
        "goal": goal,
        "context": context,
        "constraints": constraints,
        "options": options,
        "decision": decision,
        "confidence": decision["confidence"],
        "timestamp": datetime.now().isoformat(),
        "context_hash": compute_hash(context),
        "schema_version": "1.0"
    }

    return reasoning


def reflect(action_result, success):
    """
    Reflect on action result.
    """
    reflection_id = f"reflect-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"

    if success:
        analysis = "Action succeeded as expected"
        learned = "No adjustment needed"
        next_decision = "CONTINUE"
    else:
        analysis = "Action failed"
        learned = "Consider retry or alternative approach"
        next_decision = "RETRY"

    reflection = {
        "reflection_id": reflection_id,
        "action_result": action_result,
        "success": success,
        "analysis": analysis,
        "learned": learned,
        "next_decision": next_decision,
        "timestamp": datetime.now().isoformat(),
        "schema_version": "1.0"
    }

    return reflection


def main():
    print("=" * 60)
    print("TLL OS Agent Reasoning Runtime")
    print("=" * 60)
    print()

    # Demo: Reason about "Open calculator"
    goal = "Open calculator"
    print(f"Goal: {goal}")
    print()

    reasoning = reason(goal, context={"screen": "desktop"}, constraints=["no_admin"])
    print(f"Reasoning ID: {reasoning['reasoning_id']}")
    print(f"Options: {len(reasoning['options'])}")
    for i, opt in enumerate(reasoning['options']):
        print(f"  Option {i+1}: {opt['action']} -> {opt['target']} (conf: {opt['confidence']})")
    print(f"Decision: {reasoning['decision']['action']} -> {reasoning['decision']['target']}")
    print(f"Confidence: {reasoning['confidence']}")
    print()

    # Reflection demo
    print("Reflection Demo:")
    reflection = reflect({"action": "OPEN_APP", "target": "calculator"}, success=True)
    print(f"  Success: {reflection['success']}")
    print(f"  Analysis: {reflection['analysis']}")
    print(f"  Next: {reflection['next_decision']}")
    print()

    # Save evidence
    output_dir = SCRIPT_DIR / "decisions"
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "latest_reasoning.json", "w", encoding="utf-8") as f:
        json.dump(reasoning, f, indent=2, ensure_ascii=False)
    with open(output_dir / "latest_reflection.json", "w", encoding="utf-8") as f:
        json.dump(reflection, f, indent=2, ensure_ascii=False)

    print(f"Reasoning saved: latest_reasoning.json")
    print(f"Reflection saved: latest_reflection.json")
    sys.exit(0)


if __name__ == "__main__":
    main()
