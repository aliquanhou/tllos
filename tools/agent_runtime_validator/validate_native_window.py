#!/usr/bin/env python3
"""
TLL OS Native Window Validator

5 Gates:
  Gate 1: Window File Exists
  Gate 2: No PySide6 in Window
  Gate 3: No Qt in Window
  Gate 4: Win32 API Calls
  Gate 5: GDI Rendering
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
WINDOW_FILE = PROJECT_ROOT / "tllos" / "native" / "desktop" / "native_window_host.py"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_window_exists():
    """Gate 1: Window file exists"""
    if WINDOW_FILE.exists():
        results.append(("Gate 1: Window File", PASS))
        return True
    results.append(("Gate 1: Window File", FAIL))
    return False


def gate2_no_pyside6():
    """Gate 2: No PySide6 import"""
    with open(WINDOW_FILE, 'r') as f:
        lines = f.readlines()
    import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
    for line in import_lines:
        if 'PySide6' in line:
            results.append(("Gate 2: No PySide6", FAIL))
            return False
    results.append(("Gate 2: No PySide6", PASS))
    return True


def gate3_no_qt():
    """Gate 3: No Qt import"""
    with open(WINDOW_FILE, 'r') as f:
        lines = f.readlines()
    import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
    for line in import_lines:
        if 'Qt' in line or 'qt' in line:
            results.append(("Gate 3: No Qt", FAIL))
            return False
    results.append(("Gate 3: No Qt", PASS))
    return True


def gate4_win32_api():
    """Gate 4: Win32 API calls present"""
    with open(WINDOW_FILE, 'r') as f:
        content = f.read()
    if 'RegisterClassExW' in content and 'CreateWindowExW' in content and 'DefWindowProcW' in content:
        results.append(("Gate 4: Win32 API", PASS))
        return True
    results.append(("Gate 4: Win32 API", FAIL))
    return False


def gate5_gdi_rendering():
    """Gate 5: GDI rendering present"""
    with open(WINDOW_FILE, 'r') as f:
        content = f.read()
    if 'BeginPaint' in content and 'FillRect' in content and 'DrawTextW' in content:
        results.append(("Gate 5: GDI Rendering", PASS))
        return True
    results.append(("Gate 5: GDI Rendering", FAIL))
    return False


def main():
    print("=" * 60)
    print("TLL OS Native Window Validator")
    print("=" * 60)
    print()

    gate1_window_exists()
    gate2_no_pyside6()
    gate3_no_qt()
    gate4_win32_api()
    gate5_gdi_rendering()

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
