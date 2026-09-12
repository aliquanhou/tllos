#!/usr/bin/env python3
"""
TLL OS EXE Packaging Validator

5 Gates:
  Gate 1: PyInstaller Installed
  Gate 2: Build Script Exists
  Gate 3: EXE File Exists
  Gate 4: EXE Size Reasonable
  Gate 5: Safety Boundary
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_pyinstaller():
    """Gate 1: PyInstaller installed"""
    try:
        import PyInstaller
        results.append(("Gate 1: PyInstaller", PASS))
        return True
    except ImportError:
        results.append(("Gate 1: PyInstaller", FAIL))
        return False


def gate2_build_script():
    """Gate 2: Build script exists"""
    try:
        script = PROJECT_ROOT / "build_exe.py"
        if script.exists():
            results.append(("Gate 2: Build Script", PASS))
            return True
        results.append(("Gate 2: Build Script", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 2: Build Script", f"FAIL: {e}"))
        return False


def gate3_exe_exists():
    """Gate 3: EXE file exists"""
    try:
        exe = PROJECT_ROOT / "tll-agent-desktop" / "dist" / "TLL-Agent.exe"
        if exe.exists():
            results.append(("Gate 3: EXE Exists", PASS))
            return True
        results.append(("Gate 3: EXE Exists", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 3: EXE Exists", f"FAIL: {e}"))
        return False


def gate4_exe_size():
    """Gate 4: EXE size reasonable (> 10MB)"""
    try:
        exe = PROJECT_ROOT / "tll-agent-desktop" / "dist" / "TLL-Agent.exe"
        if exe.exists():
            size_mb = exe.stat().st_size / (1024 * 1024)
            if size_mb > 10:
                results.append(("Gate 4: EXE Size", PASS))
                return True
        results.append(("Gate 4: EXE Size", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 4: EXE Size", f"FAIL: {e}"))
        return False


def gate5_safety():
    """Gate 5: Safety boundary"""
    try:
        launcher = PROJECT_ROOT / "tll-agent-desktop" / "launcher" / "start_agent.py"
        with open(launcher, 'r') as f:
            content = f.read()
        if "import pyautogui" not in content:
            results.append(("Gate 5: Safety", PASS))
            return True
        results.append(("Gate 5: Safety", FAIL))
        return False
    except Exception as e:
        results.append(("Gate 5: Safety", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS EXE Packaging Validator")
    print("=" * 60)
    print()

    gate1_pyinstaller()
    gate2_build_script()
    gate3_exe_exists()
    gate4_exe_size()
    gate5_safety()

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
