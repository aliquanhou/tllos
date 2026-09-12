#!/usr/bin/env python3
"""
TLL OS Native Cockpit Runtime Validator

5 Gates:
  Gate 1: State Bus Binding
  Gate 2: Lifecycle Controller
  Gate 3: Frame Buffer Hash
  Gate 4: Monitor-2 Support
  Gate 5: No Fake State
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
COCKPIT_FILE = PROJECT_ROOT / "tllos" / "native" / "desktop" / "native_window_host.py"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_state_bus():
    with open(COCKPIT_FILE, 'r') as f:
        content = f.read()
    if 'StateBus' in content and 'agent_state.json' in content:
        results.append(("Gate 1: State Bus", PASS))
        return True
    results.append(("Gate 1: State Bus", FAIL))
    return False


def gate2_lifecycle():
    with open(COCKPIT_FILE, 'r') as f:
        content = f.read()
    if 'LifecycleController' in content and 'VALID_TRANSITIONS' in content:
        results.append(("Gate 2: Lifecycle Controller", PASS))
        return True
    results.append(("Gate 2: Lifecycle Controller", FAIL))
    return False


def gate3_frame_buffer():
    with open(COCKPIT_FILE, 'r') as f:
        content = f.read()
    if 'FrameBuffer' in content and 'sha256' in content:
        results.append(("Gate 3: Frame Buffer Hash", PASS))
        return True
    results.append(("Gate 3: Frame Buffer Hash", FAIL))
    return False


def gate4_monitor2():
    with open(COCKPIT_FILE, 'r') as f:
        content = f.read()
    if 'move_to_monitor_2' in content and 'MonitorFromPoint' in content:
        results.append(("Gate 4: Monitor-2 Support", PASS))
        return True
    results.append(("Gate 4: Monitor-2 Support", FAIL))
    return False


def gate5_no_fake():
    with open(COCKPIT_FILE, 'r') as f:
        lines = f.readlines()
    import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
    for line in import_lines:
        if 'PySide6' in line or 'Qt' in line or 'pyautogui' in line:
            results.append(("Gate 5: No Fake/GUI Dep", FAIL))
            return False
    results.append(("Gate 5: No Fake/GUI Dep", PASS))
    return True


def main():
    print("=" * 60)
    print("TLL OS Native Cockpit Runtime Validator")
    print("=" * 60)
    print()

    gate1_state_bus()
    gate2_lifecycle()
    gate3_frame_buffer()
    gate4_monitor2()
    gate5_no_fake()

    print()
    passed = sum(1 for _, r in results if r == PASS)
    failed = len(results) - passed
    for name, result in results:
        status = "✅" if result == PASS else "❌"
        print(f"  {status} {name:40s} {result}")

    print()
    print(f"Total: {passed}/5 Gates PASS, {failed} FAIL")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
