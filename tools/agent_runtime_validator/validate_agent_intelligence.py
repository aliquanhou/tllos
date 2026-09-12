#!/usr/bin/env python3
"""
TLL OS Agent Intelligence Validator

Gates:
- Gate 1: Reasoning Schema
- Gate 2: Decision Evidence
- Gate 3: Confidence Gate
- Gate 4: Reflection Loop
- Gate 5: Safety Boundary
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
    print("TLL OS Agent Intelligence Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Reasoning Schema
    print("--- Gate 1: Reasoning Schema ---")
    ok, schema = validate_json_file("tllos/agent_runtime/intelligence/reasoning_model.json")
    if not ok:
        print(f"  >> FAIL: {schema}")
        all_passed = False
        results.append(("Gate 1: Reasoning Schema", "FAIL"))
    else:
        required = ["reasoning_id", "goal", "context", "options", "decision", "confidence"]
        missing = [f for f in required if f not in schema]
        if missing:
            print(f"  >> FAIL: missing: {missing}")
            all_passed = False
            results.append(("Gate 1: Reasoning Schema", "FAIL"))
        else:
            print(f"  >> PASS: reasoning schema valid")
            results.append(("Gate 1: Reasoning Schema", "PASS"))

    # Gate 2: Decision Evidence
    print()
    print("--- Gate 2: Decision Evidence ---")
    decisions_dir = os.path.join(PROJECT_ROOT, "tllos/agent_runtime/intelligence/decisions")
    reasoning_path = os.path.join(decisions_dir, "latest_reasoning.json")
    if not os.path.exists(reasoning_path):
        print(f"  >> FAIL: no decision evidence")
        all_passed = False
        results.append(("Gate 2: Decision Evidence", "FAIL"))
    else:
        with open(reasoning_path, 'r') as f:
            reasoning = json.load(f)
        if "reasoning_id" in reasoning and "decision" in reasoning:
            print(f"  Reasoning ID: {reasoning['reasoning_id']}")
            print(f"  Decision: {reasoning['decision']['action']}")
            print(f"  >> PASS: decision evidence present")
            results.append(("Gate 2: Decision Evidence", "PASS"))
        else:
            print(f"  >> FAIL: decision fields missing")
            all_passed = False
            results.append(("Gate 2: Decision Evidence", "FAIL"))

    # Gate 3: Confidence Gate
    print()
    print("--- Gate 3: Confidence Gate ---")
    ok, reasoning = validate_json_file("tllos/agent_runtime/intelligence/decisions/latest_reasoning.json")
    if not ok:
        print(f"  >> FAIL: {reasoning}")
        all_passed = False
        results.append(("Gate 3: Confidence Gate", "FAIL"))
    else:
        conf = reasoning.get("confidence", 0)
        print(f"  Confidence: {conf}")
        if conf >= 0.5:
            print(f"  >> PASS: confidence >= 0.5")
            results.append(("Gate 3: Confidence Gate", "PASS"))
        else:
            print(f"  >> FAIL: confidence too low")
            all_passed = False
            results.append(("Gate 3: Confidence Gate", "FAIL"))

    # Gate 4: Reflection Loop
    print()
    print("--- Gate 4: Reflection Loop ---")
    reflection_path = os.path.join(decisions_dir, "latest_reflection.json")
    if not os.path.exists(reflection_path):
        print(f"  >> FAIL: no reflection evidence")
        all_passed = False
        results.append(("Gate 4: Reflection Loop", "FAIL"))
    else:
        with open(reflection_path, 'r') as f:
            reflection = json.load(f)
        if "success" in reflection and "next_decision" in reflection:
            print(f"  Success: {reflection['success']}")
            print(f"  Next: {reflection['next_decision']}")
            print(f"  >> PASS: reflection loop present")
            results.append(("Gate 4: Reflection Loop", "PASS"))
        else:
            print(f"  >> FAIL: reflection fields missing")
            all_passed = False
            results.append(("Gate 4: Reflection Loop", "FAIL"))

    # Gate 5: Safety Boundary
    print()
    print("--- Gate 5: Safety Boundary ---")
    arch_path = os.path.join(PROJECT_ROOT, "tllos/agent_runtime/intelligence/architecture.md")
    if os.path.exists(arch_path):
        with open(arch_path, 'r') as f:
            content = f.read()
        if "Forbidden" in content and "Brain → OS" in content:
            print(f"  >> PASS: safety boundary defined")
            results.append(("Gate 5: Safety Boundary", "PASS"))
        else:
            print(f"  >> FAIL: safety boundary missing")
            all_passed = False
            results.append(("Gate 5: Safety Boundary", "FAIL"))
    else:
        print(f"  >> FAIL: architecture missing")
        all_passed = False
        results.append(("Gate 5: Safety Boundary", "FAIL"))

    print()
    print("=" * 60)
    if all_passed:
        print("Agent Intelligence Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        sys.exit(0)
    else:
        print("Agent Intelligence Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        sys.exit(1)


if __name__ == "__main__":
    main()
