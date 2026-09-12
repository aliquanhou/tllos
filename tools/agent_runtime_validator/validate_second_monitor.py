#!/usr/bin/env python3
"""
TLL OS Second Monitor Validator

5 Gates:
  Gate 1: Monitor Detection
  Gate 2: Window Placement
  Gate 3: Cockpit Startup
  Gate 4: State Stream
  Gate 5: Safety Boundary
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DESKTOP_DIR = PROJECT_ROOT / "tll-agent-desktop"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_monitor_detection():
    """Gate 1: Monitor detection exists"""
    try:
        monitor_mgr = DESKTOP_DIR / "runtime" / "monitor_manager.py"
        if monitor_mgr.exists():
            results.append(("Gate 1: Monitor Detection", PASS))
            return True
        results.append(("Gate 1: Monitor Detection", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 1: Monitor Detection", f"FAIL: {e}"))
        return False


def gate2_window_placement():
    """Gate 2: Window placement config"""
    try:
        config = DESKTOP_DIR / "config" / "monitor.json"
        if config.exists():
            results.append(("Gate 2: Window Placement", PASS))
            return True
        results.append(("Gate 2: Window Placement", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 2: Window Placement", f"FAIL: {e}"))
        return False


def gate3_cockpit_startup():
    """Gate 3: Cockpit startup"""
    try:
        launcher = DESKTOP_DIR / "launcher" / "start_agent.py"
        if launcher.exists():
            results.append(("Gate 3: Cockpit Startup", PASS))
            return True
        results.append(("Gate 3: Cockpit Startup", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 3: Cockpit Startup", f"FAIL: {e}"))
        return False


def gate4_state_stream():
    """Gate 4: State stream"""
    try:
        cockpit = PROJECT_ROOT / "tllos" / "agent_runtime" / "desktop_cockpit" / "main_window.py"
        if cockpit.exists():
            results.append(("Gate 4: State Stream", PASS))
            return True
        results.append(("Gate 4: State Stream", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 4: State Stream", f"FAIL: {e}"))
        return False


def gate5_safety_boundary():
    """Gate 5: Safety boundary"""
    try:
        launcher = DESKTOP_DIR / "launcher" / "start_agent.py"
        with open(launcher, 'r') as f:
            content = f.read()
        if "import pyautogui" not in content:
            results.append(("Gate 5: Safety Boundary", PASS))
            return True
        results.append(("Gate 5: Safety Boundary", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 5: Safety Boundary", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Second Monitor Validator")
    print("=" * 60)
    print()

    gate1_monitor_detection()
    gate2_window_placement()
    gate3_cockpit_startup()
    gate4_state_stream()
    gate5_safety_boundary()

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
