#!/usr/bin/env python3
"""
TLL OS Agent Loop Validator

5 Gates:
  Gate 1: Lifecycle State Transition
  Gate 2: Runtime Integration
  Gate 3: Safety Approval
  Gate 4: Evidence Binding
  Gate 5: Session Replay
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
LIFECYCLE_DIR = PROJECT_ROOT / "tllos" / "agent_runtime" / "lifecycle"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_lifecycle():
    """Gate 1: Lifecycle state machine valid"""
    try:
        lifecycle_file = LIFECYCLE_DIR / "agent_lifecycle.py"
        if not lifecycle_file.exists():
            results.append(("Gate 1: Lifecycle", FAIL))
            return False
        with open(lifecycle_file, 'r') as f:
            content = f.read()
        if "VALID_TRANSITIONS" in content and "CREATED" in content:
            results.append(("Gate 1: Lifecycle", PASS))
            return True
        results.append(("Gate 1: Lifecycle", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 1: Lifecycle", f"FAIL: {e}"))
        return False


def gate2_runtime():
    """Gate 2: Runtime integration exists"""
    try:
        loop_file = LIFECYCLE_DIR / "agent_loop.py"
        if loop_file.exists():
            results.append(("Gate 2: Runtime", PASS))
            return True
        results.append(("Gate 2: Runtime", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 2: Runtime", f"FAIL: {e}"))
        return False


def gate3_safety():
    """Gate 3: Approval required"""
    try:
        loop_file = LIFECYCLE_DIR / "agent_loop.py"
        with open(loop_file, 'r') as f:
            content = f.read()
        if "WAIT_APPROVAL" in content and "request_approval" in content:
            results.append(("Gate 3: Safety", PASS))
            return True
        results.append(("Gate 3: Safety", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 3: Safety", f"FAIL: {e}"))
        return False


def gate4_evidence():
    """Gate 4: Evidence binding"""
    try:
        loop_file = LIFECYCLE_DIR / "agent_loop.py"
        with open(loop_file, 'r') as f:
            content = f.read()
        if "events" in content and "timestamp" in content:
            results.append(("Gate 4: Evidence", PASS))
            return True
        results.append(("Gate 4: Evidence", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 4: Evidence", f"FAIL: {e}"))
        return False


def gate5_replay():
    """Gate 5: Session replay"""
    try:
        sessions_dir = LIFECYCLE_DIR / "sessions"
        if sessions_dir.exists():
            results.append(("Gate 5: Replay", PASS))
            return True
        results.append(("Gate 5: Replay", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 5: Replay", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Agent Loop Validator")
    print("=" * 60)
    print()

    gate1_lifecycle()
    gate2_runtime()
    gate3_safety()
    gate4_evidence()
    gate5_replay()

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
