#!/usr/bin/env python3
"""
TLL OS Native Window Manager Validator

5 Gates:
  Gate 1: Window Object
  Gate 2: Window Manager Operations
  Gate 3: Compositor
  Gate 4: Multi-window Screenshot
  Gate 5: No OS Window API
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

VM_DIR = PROJECT_ROOT / "tllos" / "virtual_machine"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_window_object():
    try:
        from tllos.virtual_machine import TLLWindow
        win = TLLWindow(id="test", title="Test", x=10, y=10, width=100, height=100)
        if win.id == "test" and win.width == 100 and win.buffer.shape == (100, 100, 3):
            results.append(("Gate 1: Window Object", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Window Object", FAIL))
    return False


def gate2_window_manager():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager
        fb = TLLFramebuffer(800, 600)
        wm = TLLWindowManager(fb)
        w1 = wm.create_window("W1", 0, 0, 100, 100)
        w2 = wm.create_window("W2", 50, 50, 100, 100)

        # Test operations
        wm.move_window(w1.id, 200, 200)
        wm.resize_window(w2.id, 200, 200)
        wm.focus_window(w1)

        if w1.x == 200 and w2.width == 200 and wm.focused_window == w1:
            results.append(("Gate 2: Window Manager", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Window Manager", FAIL))
    return False


def gate3_compositor():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
        fb = TLLFramebuffer(800, 600)
        wm = TLLWindowManager(fb)
        comp = TLLCompositor(wm)

        w1 = wm.create_window("W1", 0, 0, 200, 200)
        w1.clear(255, 0, 0)
        w2 = wm.create_window("W2", 100, 100, 200, 200)
        w2.clear(0, 255, 0)

        result = comp.composite()
        if result["windows"] == 2 and result["hash"]:
            results.append(("Gate 3: Compositor", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Compositor", FAIL))
    return False


def gate4_multi_window_screenshot():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor, TLLDesktopSurface
        fb = TLLFramebuffer(800, 600)
        wm = TLLWindowManager(fb)
        comp = TLLCompositor(wm)

        wm.create_window("W1", 0, 0, 200, 200)
        wm.create_window("W2", 300, 200, 200, 200)
        comp.composite()

        surface = TLLDesktopSurface(fb)
        output = PROJECT_ROOT / "test_window_ss.png"
        result = surface.export_screenshot(output)
        if result["path"] and output.exists():
            output.unlink()
            results.append(("Gate 4: Multi-window Screenshot", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Multi-window Screenshot", FAIL))
    return False


def gate5_no_os_window_api():
    """Check no Windows HWND or Qt window imports."""
    try:
        fpath = VM_DIR / "window_system.py"
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'ctypes' in content or 'user32' in content or 'HWND' in content:
            results.append(("Gate 5: No OS Window API", FAIL))
            return False
        results.append(("Gate 5: No OS Window API", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: No OS Window API", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Native Window Manager Validator")
    print("=" * 60)
    print()

    gate1_window_object()
    gate2_window_manager()
    gate3_compositor()
    gate4_multi_window_screenshot()
    gate5_no_os_window_api()

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
