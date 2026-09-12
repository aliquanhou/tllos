#!/usr/bin/env python3
"""
TLL OS Vision Memory Validator

Gates:
- Gate 1: Memory Schema
- Gate 2: Memory Content
- Gate 3: Replay Verification
- Gate 4: Memory Boundary
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
    print("TLL OS Vision Memory Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Memory Schema
    print("--- Gate 1: Memory Schema ---")
    ok, schema = validate_json_file("tllos/agent_runtime/desktop_vision_runtime/vision_memory.json")
    if not ok:
        print(f"  >> FAIL: {schema}")
        all_passed = False
        results.append(("Gate 1: Memory Schema", "FAIL"))
    else:
        required = ["memory_id", "frames", "objects", "memory_boundary", "schema_version"]
        missing = [f for f in required if f not in schema]
        if missing:
            print(f"  >> FAIL: missing: {missing}")
            all_passed = False
            results.append(("Gate 1: Memory Schema", "FAIL"))
        else:
            print(f"  >> PASS: memory schema valid")
            results.append(("Gate 1: Memory Schema", "PASS"))

    # Gate 2: Memory Content
    print()
    print("--- Gate 2: Memory Content ---")
    ok, memory = validate_json_file("tllos/agent_runtime/desktop_vision_runtime/vision_memory.json")
    if not ok:
        print(f"  >> FAIL: {memory}")
        all_passed = False
        results.append(("Gate 2: Memory Content", "FAIL"))
    else:
        frame_count = len(memory.get("frames", []))
        obj_count = len(memory.get("objects", []))
        print(f"  Frames: {frame_count}")
        print(f"  Objects: {obj_count}")
        if frame_count > 0:
            print(f"  >> PASS: memory has content")
            results.append(("Gate 2: Memory Content", "PASS"))
        else:
            print(f"  >> FAIL: memory empty")
            all_passed = False
            results.append(("Gate 2: Memory Content", "FAIL"))

    # Gate 3: Replay Verification
    print()
    print("--- Gate 3: Replay Verification ---")
    replay = memory.get("replay_verification", [])
    if not replay:
        print(f"  >> FAIL: no replay verification data")
        all_passed = False
        results.append(("Gate 3: Replay Verification", "FAIL"))
    else:
        all_match = all(r.get("match", False) for r in replay)
        if all_match:
            print(f"  Replay checks: {len(replay)} all PASS")
            print(f"  >> PASS: replay verified")
            results.append(("Gate 3: Replay Verification", "PASS"))
        else:
            print(f"  >> FAIL: replay mismatch detected")
            all_passed = False
            results.append(("Gate 3: Replay Verification", "FAIL"))

    # Gate 4: Memory Boundary
    print()
    print("--- Gate 4: Memory Boundary ---")
    boundary = memory.get("memory_boundary", {})
    can_observe = boundary.get("can_observe_history", False)
    can_act = boundary.get("can_make_action_decision", True)
    print(f"  can_observe_history: {can_observe}")
    print(f"  can_make_action_decision: {can_act}")
    if can_observe and not can_act:
        print(f"  >> PASS: memory boundary correct (observe only)")
        results.append(("Gate 4: Memory Boundary", "PASS"))
    else:
        print(f"  >> FAIL: memory boundary incorrect")
        all_passed = False
        results.append(("Gate 4: Memory Boundary", "FAIL"))

    print()
    print("=" * 60)
    if all_passed:
        print("Vision Memory Validation PASS")
        print(f"  4/4 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        sys.exit(0)
    else:
        print("Vision Memory Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        sys.exit(1)


if __name__ == "__main__":
    main()
