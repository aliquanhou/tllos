#!/usr/bin/env python3
"""
TLL OS Virtual Display Reality Validator

5 Gates:
  Gate 1: Virtual Framebuffer
  Gate 2: Pixel Rendering
  Gate 3: Desktop Surface
  Gate 4: Screenshot Export
  Gate 5: No OS Dependency
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


def gate1_framebuffer():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        fb = TLLFramebuffer(800, 600)
        fb.clear(255, 0, 0)
        fb.put_pixel(100, 100, 0, 255, 0)
        result = fb.commit()
        if result["frame"] == 1 and result["hash"]:
            results.append(("Gate 1: Virtual Framebuffer", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Virtual Framebuffer", FAIL))
    return False


def gate2_pixel_rendering():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        import numpy as np
        fb = TLLFramebuffer(100, 100)
        fb.fill_rect(10, 10, 50, 50, 255, 255, 255)
        fb.draw_rect(0, 0, 100, 100, 255, 0, 0, 2)
        data = fb.get_pixel_data()
        # Check center pixel is white
        if data[35, 35, 0] == 255:
            results.append(("Gate 2: Pixel Rendering", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Pixel Rendering", FAIL))
    return False


def gate3_desktop_surface():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLDesktopSurface
        fb = TLLFramebuffer(800, 600)
        surface = TLLDesktopSurface(fb)
        result = surface.render_desktop()
        if result["frame"] == 1 and result["hash"]:
            results.append(("Gate 3: Desktop Surface", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Desktop Surface", FAIL))
    return False


def gate4_screenshot_export():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLDesktopSurface
        fb = TLLFramebuffer(800, 600)
        surface = TLLDesktopSurface(fb)
        surface.render_desktop()
        output = PROJECT_ROOT / "test_display_export.png"
        result = surface.export_screenshot(output)
        if result["path"] and output.exists():
            output.unlink()
            results.append(("Gate 4: Screenshot Export", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Screenshot Export", FAIL))
    return False


def gate5_no_os_dep():
    """Check no Windows API imports in VM display layer."""
    try:
        display_files = ["framebuffer.py", "desktop_surface.py"]
        for fname in display_files:
            fpath = VM_DIR / fname
            with open(fpath, 'r', encoding='utf-8') as f:
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
    print("TLL OS Virtual Display Reality Validator")
    print("=" * 60)
    print()

    gate1_framebuffer()
    gate2_pixel_rendering()
    gate3_desktop_surface()
    gate4_screenshot_export()
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
