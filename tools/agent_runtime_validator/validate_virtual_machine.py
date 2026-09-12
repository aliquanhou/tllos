#!/usr/bin/env python3
"""
TLL OS Virtual Machine Validator

5 Gates:
  Gate 1: Virtual Hardware
  Gate 2: Window Manager
  Gate 3: Renderer + Display Buffer
  Gate 4: Boot Sequence
  Gate 5: No OS Dependency
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
VM_DIR = PROJECT_ROOT / "tllos" / "virtual_machine"

# Add project root to path
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_virtual_hardware():
    try:
        from tllos.virtual_machine import VirtualHardware
        hw = VirtualHardware()
        result = hw.boot()
        if result["status"] == "HARDWARE_READY":
            results.append(("Gate 1: Virtual Hardware", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Virtual Hardware", FAIL))
    return False


def gate2_window_manager():
    try:
        from tllos.virtual_machine import TLLWindowManager, VirtualDisplay
        display = VirtualDisplay()
        wm = TLLWindowManager(display)
        win = wm.create_window("Test", 100, 100, 800, 600)
        if win.id and win.title == "Test":
            results.append(("Gate 2: Window Manager", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Window Manager", FAIL))
    return False


def gate3_renderer():
    try:
        from tllos.virtual_machine import TLLRenderer, TLLDisplayBuffer, VirtualDisplay, TLLWindowManager
        display = VirtualDisplay()
        wm = TLLWindowManager(display)
        renderer = TLLRenderer(display, wm)
        buffer = TLLDisplayBuffer(display)
        result = buffer.commit(renderer)
        if result["frame_id"] == 1 and result["hash"]:
            results.append(("Gate 3: Renderer + Buffer", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Renderer + Buffer", FAIL))
    return False


def gate4_boot_sequence():
    try:
        from tllos.virtual_machine import TLLOSVirtualMachine
        vm = TLLOSVirtualMachine()
        result = vm.boot()
        if result["state"] == "DESKTOP_READY" and len(result["boot_steps"]) == 6:
            results.append(("Gate 4: Boot Sequence", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Boot Sequence", FAIL))
    return False


def gate5_no_os_dep():
    """Check no Windows API imports in VM package."""
    try:
        for pyfile in VM_DIR.glob("*.py"):
            with open(pyfile, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
            for line in import_lines:
                if 'ctypes' in line or 'user32' in line or 'gdi32' in line:
                    results.append(("Gate 5: No OS Dependency", FAIL))
                    return False
        results.append(("Gate 5: No OS Dependency", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: No OS Dependency", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Virtual Machine Validator")
    print("=" * 60)
    print()

    gate1_virtual_hardware()
    gate2_window_manager()
    gate3_renderer()
    gate4_boot_sequence()
    gate5_no_os_dep()

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
