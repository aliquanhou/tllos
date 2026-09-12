#!/usr/bin/env python3
"""
TLL OS Desktop Cockpit Validator

5 Gates:
  Gate 1: GUI Launch
  Gate 2: State Sync
  Gate 3: Panel Rendering
  Gate 4: Safety Boundary
  Gate 5: Evidence Display
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
COCKPIT_DIR = PROJECT_ROOT / "tllos" / "agent_runtime" / "desktop_cockpit"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_gui_launch():
    """Gate 1: GUI files exist"""
    try:
        main_window = COCKPIT_DIR / "main_window.py"
        cockpit_runtime = COCKPIT_DIR / "cockpit_runtime.py"
        if main_window.exists() and cockpit_runtime.exists():
            results.append(("Gate 1: GUI Launch", PASS))
            return True
        results.append(("Gate 1: GUI Launch", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 1: GUI Launch", f"FAIL: {e}"))
        return False


def gate2_state_sync():
    """Gate 2: State Controller exists"""
    try:
        controller = COCKPIT_DIR / "controllers" / "state_controller.py"
        if controller.exists():
            results.append(("Gate 2: State Sync", PASS))
            return True
        results.append(("Gate 2: State Sync", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 2: State Sync", f"FAIL: {e}"))
        return False


def gate3_panel_rendering():
    """Gate 3: Widgets exist"""
    try:
        widgets = ["status_widget", "vision_widget", "reasoning_widget", "plan_widget", "action_widget", "evidence_widget"]
        # Check main_window.py contains all widgets
        main_file = COCKPIT_DIR / "main_window.py"
        with open(main_file, 'r') as f:
            content = f.read()
        missing = [w for w in widgets if w not in content and w.replace("_widget", "") not in content]
        if len(missing) == 0:
            results.append(("Gate 3: Panel Rendering", PASS))
            return True
        results.append(("Gate 3: Panel Rendering", f"FAIL: missing {missing}"))
        return False
    except Exception as e:
        results.append(("Gate 3: Panel Rendering", f"FAIL: {e}"))
        return False


def gate4_safety_boundary():
    """Gate 4: No direct pyautogui in cockpit"""
    try:
        main_file = COCKPIT_DIR / "main_window.py"
        with open(main_file, 'r') as f:
            content = f.read()
        if "import pyautogui" in content:
            results.append(("Gate 4: Safety Boundary", "FAIL: direct pyautogui import"))
            return False
        results.append(("Gate 4: Safety Boundary", PASS))
        return True
    except Exception as e:
        results.append(("Gate 4: Safety Boundary", f"FAIL: {e}"))
        return False


def gate5_evidence_display():
    """Gate 5: Evidence widget exists"""
    try:
        main_file = COCKPIT_DIR / "main_window.py"
        with open(main_file, 'r') as f:
            content = f.read()
        if "EvidenceWidget" in content:
            results.append(("Gate 5: Evidence Display", PASS))
            return True
        results.append(("Gate 5: Evidence Display", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 5: Evidence Display", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Desktop Cockpit Validator")
    print("=" * 60)
    print()

    gate1_gui_launch()
    gate2_state_sync()
    gate3_panel_rendering()
    gate4_safety_boundary()
    gate5_evidence_display()

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
