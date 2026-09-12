#!/usr/bin/env python3
"""
TLL OS Native Desktop Validator

5 Gates:
  Gate 1: Native Monitor (no PySide6)
  Gate 2: Native Window
  Gate 3: Native Screenshot
  Gate 4: Native Input Boundary
  Gate 5: No Python GUI Dependency
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
NATIVE_DIR = PROJECT_ROOT / "tllos" / "native" / "desktop"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_native_monitor():
    """Gate 1: Native monitor exists without PySide6"""
    try:
        monitor_file = NATIVE_DIR / "native_monitor.py"
        if not monitor_file.exists():
            results.append(("Gate 1: Native Monitor", FAIL))
            return False
        with open(monitor_file, 'r') as f:
            lines = f.readlines()
        # Check only import lines, not comments
        import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
        for line in import_lines:
            if 'PySide6' in line or 'QApplication' in line:
                results.append(("Gate 1: Native Monitor", FAIL))
                return False
        content = ''.join(lines)
        if "EnumDisplayMonitors" in content or "user32" in content:
            results.append(("Gate 1: Native Monitor", PASS))
            return True
        results.append(("Gate 1: Native Monitor", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 1: Native Monitor", f"FAIL: {e}"))
        return False


def gate2_native_window():
    """Gate 2: Native window placement"""
    try:
        window_file = NATIVE_DIR / "native_window.py"
        if not window_file.exists():
            results.append(("Gate 2: Native Window", FAIL))
            return False
        with open(window_file, 'r') as f:
            content = f.read()
        if "MoveWindow" in content or "SetWindowPos" in content:
            results.append(("Gate 2: Native Window", PASS))
            return True
        results.append(("Gate 2: Native Window", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 2: Native Window", f"FAIL: {e}"))
        return False


def gate3_native_screenshot():
    """Gate 3: Native screenshot"""
    try:
        shot_file = NATIVE_DIR / "native_screenshot.py"
        if not shot_file.exists():
            results.append(("Gate 3: Native Screenshot", FAIL))
            return False
        with open(shot_file, 'r') as f:
            content = f.read()
        if "BitBlt" in content or "GetDC" in content:
            results.append(("Gate 3: Native Screenshot", PASS))
            return True
        results.append(("Gate 3: Native Screenshot", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 3: Native Screenshot", f"FAIL: {e}"))
        return False


def gate4_input_boundary():
    """Gate 4: Native input boundary"""
    try:
        input_file = NATIVE_DIR / "native_input.py"
        if not input_file.exists():
            results.append(("Gate 4: Input Boundary", FAIL))
            return False
        with open(input_file, 'r') as f:
            content = f.read()
        if "SendInput" in content and "PERMISSION_DENIED" in content:
            results.append(("Gate 4: Input Boundary", PASS))
            return True
        results.append(("Gate 4: Input Boundary", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 4: Input Boundary", f"FAIL: {e}"))
        return False


def gate5_no_gui_dependency():
    """Gate 5: No Python GUI dependency in native layer"""
    try:
        for pyfile in NATIVE_DIR.glob("*.py"):
            with open(pyfile, 'r') as f:
                lines = f.readlines()
            import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
            for line in import_lines:
                if "PySide6" in line or "pyautogui" in line:
                    results.append(("Gate 5: No GUI Dep", FAIL))
                    return False
        results.append(("Gate 5: No GUI Dep", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: No GUI Dep", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Native Desktop Validator")
    print("=" * 60)
    print()

    gate1_native_monitor()
    gate2_native_window()
    gate3_native_screenshot()
    gate4_input_boundary()
    gate5_no_gui_dependency()

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
