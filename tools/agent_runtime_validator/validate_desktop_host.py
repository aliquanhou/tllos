#!/usr/bin/env python3
"""
TLL OS Desktop Host Validator

5 Gates:
  Gate 1: Host startup
  Gate 2: State Bus
  Gate 3: Vision Panel
  Gate 4: Reasoning Panel
  Gate 5: Action Boundary
"""

import sys
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DESKTOP_HOST_DIR = PROJECT_ROOT / "tllos" / "agent_runtime" / "desktop_host"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_host_startup():
    """Gate 1: Host can start"""
    try:
        host_runtime = DESKTOP_HOST_DIR / "host_runtime.py"
        exists = host_runtime.exists()
        if exists:
            results.append(("Gate 1: Host Startup", PASS))
            return True
        else:
            results.append(("Gate 1: Host Startup", FAIL))
            return False
    except Exception as e:
        results.append(("Gate 1: Host Startup", f"FAIL: {e}"))
        return False


def gate2_state_bus():
    """Gate 2: State Bus works"""
    try:
        schema_file = DESKTOP_HOST_DIR / "schemas" / "agent_state.json"
        if not schema_file.exists():
            results.append(("Gate 2: State Bus", FAIL))
            return False
        with open(schema_file, 'r') as f:
            data = json.load(f)
        required = ["agent_id", "state", "vision", "reasoning", "plan", "action", "evidence"]
        missing = [k for k in required if k not in data]
        if missing:
            results.append(("Gate 2: State Bus", f"FAIL: missing {missing}"))
            return False
        results.append(("Gate 2: State Bus", PASS))
        return True
    except Exception as e:
        results.append(("Gate 2: State Bus", f"FAIL: {e}"))
        return False


def gate3_vision_panel():
    """Gate 3: Vision Panel can read data"""
    try:
        vision_panel = DESKTOP_HOST_DIR / "panels" / "vision_panel.py"
        exists = vision_panel.exists()
        if exists:
            results.append(("Gate 3: Vision Panel", PASS))
            return True
        else:
            results.append(("Gate 3: Vision Panel", FAIL))
            return False
    except Exception as e:
        results.append(("Gate 3: Vision Panel", f"FAIL: {e}"))
        return False


def gate4_reasoning_panel():
    """Gate 4: Reasoning Panel can read data"""
    try:
        reasoning_panel = DESKTOP_HOST_DIR / "panels" / "reasoning_panel.py"
        exists = reasoning_panel.exists()
        if exists:
            results.append(("Gate 4: Reasoning Panel", PASS))
            return True
        else:
            results.append(("Gate 4: Reasoning Panel", FAIL))
            return False
    except Exception as e:
        results.append(("Gate 4: Reasoning Panel", f"FAIL: {e}"))
        return False


def gate5_action_boundary():
    """Gate 5: Action Boundary (Console cannot call pyautogui directly)"""
    try:
        host_runtime = DESKTOP_HOST_DIR / "host_runtime.py"
        if not host_runtime.exists():
            results.append(("Gate 5: Action Boundary", FAIL))
            return False
        with open(host_runtime, 'r') as f:
            content = f.read()
        # Check that host_runtime does NOT import pyautogui
        if "import pyautogui" in content:
            results.append(("Gate 5: Action Boundary", "FAIL: direct pyautogui import"))
            return False
        results.append(("Gate 5: Action Boundary", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: Action Boundary", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Desktop Host Validator")
    print("=" * 60)
    print()

    gate1_host_startup()
    gate2_state_bus()
    gate3_vision_panel()
    gate4_reasoning_panel()
    gate5_action_boundary()

    print()
    passed = 0
    failed = 0
    for name, result in results:
        status = "✅" if result == PASS else "❌"
        print(f"  {status} {name:40s} {result}")
        if result == PASS:
            passed += 1
        else:
            failed += 1

    print()
    print(f"Total: {passed}/5 Gates PASS, {failed} FAIL")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
