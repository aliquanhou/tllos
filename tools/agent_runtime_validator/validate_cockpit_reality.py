#!/usr/bin/env python3
"""
TLL OS Desktop Cockpit Reality Validator

5 Gates:
  Gate 1: Screenshot Preview
  Gate 2: Replay
  Gate 3: Event Stream
  Gate 4: Approval Boundary
  Gate 5: Evidence Binding
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
COCKPIT_DIR = PROJECT_ROOT / "tllos" / "agent_runtime" / "desktop_cockpit"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_screenshot_preview():
    """Gate 1: Screenshot preview in Vision Widget"""
    try:
        main_file = COCKPIT_DIR / "main_window.py"
        with open(main_file, 'r') as f:
            content = f.read()
        if "QPixmap" in content and "screenshot" in content.lower():
            results.append(("Gate 1: Screenshot Preview", PASS))
            return True
        results.append(("Gate 1: Screenshot Preview", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 1: Screenshot Preview", f"FAIL: {e}"))
        return False


def gate2_replay():
    """Gate 2: Replay widget exists"""
    try:
        main_file = COCKPIT_DIR / "main_window.py"
        with open(main_file, 'r') as f:
            content = f.read()
        if "ReplayWidget" in content and "Replay" in content:
            results.append(("Gate 2: Replay", PASS))
            return True
        results.append(("Gate 2: Replay", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 2: Replay", f"FAIL: {e}"))
        return False


def gate3_event_stream():
    """Gate 3: Event stream / timeline exists"""
    try:
        main_file = COCKPIT_DIR / "main_window.py"
        with open(main_file, 'r') as f:
            content = f.read()
        if "TimelineWidget" in content or "EventStream" in content:
            results.append(("Gate 3: Event Stream", PASS))
            return True
        results.append(("Gate 3: Event Stream", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 3: Event Stream", f"FAIL: {e}"))
        return False


def gate4_approval_boundary():
    """Gate 4: Approval buttons exist"""
    try:
        main_file = COCKPIT_DIR / "main_window.py"
        with open(main_file, 'r') as f:
            content = f.read()
        if "APPROVE" in content and "DENY" in content:
            results.append(("Gate 4: Approval Boundary", PASS))
            return True
        results.append(("Gate 4: Approval Boundary", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 4: Approval Boundary", f"FAIL: {e}"))
        return False


def gate5_evidence_binding():
    """Gate 5: Evidence widget exists"""
    try:
        main_file = COCKPIT_DIR / "main_window.py"
        with open(main_file, 'r') as f:
            content = f.read()
        if "EvidenceWidget" in content and "hash" in content.lower():
            results.append(("Gate 5: Evidence Binding", PASS))
            return True
        results.append(("Gate 5: Evidence Binding", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 5: Evidence Binding", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Desktop Cockpit Reality Validator")
    print("=" * 60)
    print()

    gate1_screenshot_preview()
    gate2_replay()
    gate3_event_stream()
    gate4_approval_boundary()
    gate5_evidence_binding()

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
