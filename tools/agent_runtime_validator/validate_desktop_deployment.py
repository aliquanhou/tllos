#!/usr/bin/env python3
"""
TLL OS Desktop Deployment Validator

5 Gates:
  Gate 1: Launcher Exists
  Gate 2: Config Exists
  Gate 3: Tamper Detection
  Gate 4: Cockpit Integration
  Gate 5: Evidence Recording
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DESKTOP_DIR = PROJECT_ROOT / "tll-agent-desktop"
LIFECYCLE_DIR = PROJECT_ROOT / "tllos" / "agent_runtime" / "lifecycle"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_launcher():
    """Gate 1: Launcher exists"""
    try:
        launcher = DESKTOP_DIR / "launcher" / "start_agent.py"
        if launcher.exists():
            results.append(("Gate 1: Launcher", PASS))
            return True
        results.append(("Gate 1: Launcher", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 1: Launcher", f"FAIL: {e}"))
        return False


def gate2_config():
    """Gate 2: Config exists"""
    try:
        config = DESKTOP_DIR / "config" / "monitor.json"
        if config.exists():
            results.append(("Gate 2: Config", PASS))
            return True
        results.append(("Gate 2: Config", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 2: Config", f"FAIL: {e}"))
        return False


def gate3_tamper():
    """Gate 3: Tamper detection exists"""
    try:
        tamper = LIFECYCLE_DIR / "tamper_detection.py"
        if tamper.exists():
            results.append(("Gate 3: Tamper Detection", PASS))
            return True
        results.append(("Gate 3: Tamper Detection", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 3: Tamper Detection", f"FAIL: {e}"))
        return False


def gate4_cockpit():
    """Gate 4: Cockpit integration"""
    try:
        cockpit = PROJECT_ROOT / "tllos" / "agent_runtime" / "desktop_cockpit" / "main_window.py"
        if cockpit.exists():
            results.append(("Gate 4: Cockpit", PASS))
            return True
        results.append(("Gate 4: Cockpit", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 4: Cockpit", f"FAIL: {e}"))
        return False


def gate5_evidence():
    """Gate 5: Evidence recording"""
    try:
        sessions = LIFECYCLE_DIR / "sessions"
        memory = LIFECYCLE_DIR / "memory"
        if sessions.exists() and memory.exists():
            results.append(("Gate 5: Evidence", PASS))
            return True
        results.append(("Gate 5: Evidence", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 5: Evidence", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Desktop Deployment Validator")
    print("=" * 60)
    print()

    gate1_launcher()
    gate2_config()
    gate3_tamper()
    gate4_cockpit()
    gate5_evidence()

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
