#!/usr/bin/env python3
"""
TLL OS Native Cockpit Validator

5 Gates:
  Gate 1: Cockpit File Exists
  Gate 2: No PySide6/Qt
  Gate 3: Win32 + GDI Rendering
  Gate 4: Screenshot Display
  Gate 5: Permission Buttons
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
COCKPIT_FILE = PROJECT_ROOT / "tllos" / "native" / "desktop" / "native_window_host.py"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_exists():
    if COCKPIT_FILE.exists():
        results.append(("Gate 1: Cockpit File", PASS))
        return True
    results.append(("Gate 1: Cockpit File", FAIL))
    return False


def gate2_no_qt():
    with open(COCKPIT_FILE, 'r') as f:
        lines = f.readlines()
    import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
    for line in import_lines:
        if 'PySide6' in line or 'Qt' in line or 'pyautogui' in line:
            results.append(("Gate 2: No Qt/pyautogui", FAIL))
            return False
    results.append(("Gate 2: No Qt/pyautogui", PASS))
    return True


def gate3_gdi_rendering():
    with open(COCKPIT_FILE, 'r') as f:
        content = f.read()
    if all(x in content for x in ['BeginPaint', 'FillRect', 'DrawTextW', 'WM_PAINT']):
        results.append(("Gate 3: GDI Rendering", PASS))
        return True
    results.append(("Gate 3: GDI Rendering", FAIL))
    return False


def gate4_screenshot():
    with open(COCKPIT_FILE, 'r') as f:
        content = f.read()
    if 'StretchBlt' in content and 'LoadImageW' in content and 'native_test.bmp' in content:
        results.append(("Gate 4: Screenshot Display", PASS))
        return True
    results.append(("Gate 4: Screenshot Display", FAIL))
    return False


def gate5_buttons():
    with open(COCKPIT_FILE, 'r') as f:
        content = f.read()
    if all(x in content for x in ['START', 'APPROVE', 'STOP', 'WM_LBUTTONDOWN']):
        results.append(("Gate 5: Permission Buttons", PASS))
        return True
    results.append(("Gate 5: Permission Buttons", FAIL))
    return False


def main():
    print("=" * 60)
    print("TLL OS Native Cockpit Validator")
    print("=" * 60)
    print()

    gate1_exists()
    gate2_no_qt()
    gate3_gdi_rendering()
    gate4_screenshot()
    gate5_buttons()

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
