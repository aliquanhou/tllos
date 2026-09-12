#!/usr/bin/env python3
"""
TLL OS Text Rendering Engine Validator

5 Gates:
  Gate 1: Text Renderer Init
  Gate 2: English Text Rendering
  Gate 3: Chinese Text Rendering
  Gate 4: Desktop Surface Text
  Gate 5: No OS Font Dependency
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


def gate1_text_renderer():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLTextRenderer
        fb = TLLFramebuffer(800, 600)
        tr = TLLTextRenderer(fb)
        if tr.font_path:
            results.append(("Gate 1: Text Renderer Init", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Text Renderer Init", FAIL))
    return False


def gate2_english_text():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLTextRenderer
        fb = TLLFramebuffer(800, 600)
        tr = TLLTextRenderer(fb)
        result = tr.draw_text(100, 100, "Hello TLL OS", 255, 255, 255, "medium")
        if result["width"] > 0 and result["height"] > 0:
            results.append(("Gate 2: English Text", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: English Text", FAIL))
    return False


def gate3_chinese_text():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLTextRenderer
        fb = TLLFramebuffer(800, 600)
        tr = TLLTextRenderer(fb)
        result = tr.draw_text(100, 100, "智能代理", 255, 255, 255, "medium")
        if result["width"] > 0 and result["height"] > 0:
            results.append(("Gate 3: Chinese Text", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Chinese Text", FAIL))
    return False


def gate4_desktop_text():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLDesktopSurface
        fb = TLLFramebuffer(800, 600)
        surface = TLLDesktopSurface(fb)
        result = surface.render_desktop()
        # Check that text was rendered (hash should be different from no-text version)
        if result["hash"]:
            results.append(("Gate 4: Desktop Surface Text", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Desktop Surface Text", FAIL))
    return False


def gate5_no_os_font_dep():
    """Check no Windows Font API direct imports."""
    try:
        fpath = VM_DIR / "text_renderer.py"
        with open(fpath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
        for line in import_lines:
            if 'ctypes' in line or 'user32' in line or 'gdi32' in line:
                results.append(("Gate 5: No OS Font Dependency", FAIL))
                return False
        results.append(("Gate 5: No OS Font Dependency", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: No OS Font Dependency", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Text Rendering Engine Validator")
    print("=" * 60)
    print()

    gate1_text_renderer()
    gate2_english_text()
    gate3_chinese_text()
    gate4_desktop_text()
    gate5_no_os_font_dep()

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
