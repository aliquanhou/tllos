#!/usr/bin/env python3
"""
TLL OS Native Cockpit Owner Experience Validator

5 Gates:
  Gate 1: Chinese UI
  Gate 2: Clipboard API
  Gate 3: Screenshot Export
  Gate 4: No GUI Dep
  Gate 5: State Bus Binding
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
COCKPIT_FILE = PROJECT_ROOT / "tllos" / "native" / "desktop" / "native_window_host.py"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_chinese_ui():
    with open(COCKPIT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    if '智能代理' in content and '视觉感知' in content and '任务规划' in content:
        results.append(("Gate 1: Chinese UI", PASS))
        return True
    results.append(("Gate 1: Chinese UI", FAIL))
    return False


def gate2_clipboard():
    with open(COCKPIT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'OpenClipboard' in content and 'SetClipboardData' in content and 'copy_to_clipboard' in content:
        results.append(("Gate 2: Clipboard API", PASS))
        return True
    results.append(("Gate 2: Clipboard API", FAIL))
    return False


def gate3_screenshot_export():
    with open(COCKPIT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'export_snapshot' in content and 'tll_snapshot' in content:
        results.append(("Gate 3: Screenshot Export", PASS))
        return True
    results.append(("Gate 3: Screenshot Export", FAIL))
    return False


def gate4_no_gui():
    with open(COCKPIT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
    for line in import_lines:
        if 'PySide6' in line or 'Qt' in line or 'pyautogui' in line:
            results.append(("Gate 4: No GUI Dep", FAIL))
            return False
    results.append(("Gate 4: No GUI Dep", PASS))
    return True


def gate5_state_bus():
    with open(COCKPIT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'StateBus' in content and 'agent_state.json' in content and 'utf-8-sig' in content:
        results.append(("Gate 5: State Bus Binding", PASS))
        return True
    results.append(("Gate 5: State Bus Binding", FAIL))
    return False


def main():
    print("=" * 60)
    print("TLL OS Owner Experience Validator")
    print("=" * 60)
    print()

    gate1_chinese_ui()
    gate2_clipboard()
    gate3_screenshot_export()
    gate4_no_gui()
    gate5_state_bus()

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
