#!/usr/bin/env python3
"""
TLL OS Native Font Runtime Validator

5 Gates:
  Gate 1: Native Font Init
  Gate 2: ASCII Glyph Rendering
  Gate 3: Chinese Glyph Rendering
  Gate 4: No External Font Dependency
  Gate 5: Desktop Surface with Native Font
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

VM_DIR = PROJECT_ROOT / "tllos" / "virtual_machine"
FONTS_DIR = VM_DIR / "fonts"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_native_font():
    try:
        from tllos.virtual_machine.fonts.tll_font import TLLFont
        font = TLLFont()
        if font.font_name == "TLL-Builtin-1.0":
            results.append(("Gate 1: Native Font Init", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Native Font Init", FAIL))
    return False


def gate2_ascii_glyphs():
    try:
        from tllos.virtual_machine.fonts.tll_font import TLLFont
        font = TLLFont()
        # Check some ASCII chars
        for c in ['A', 'B', '1', 'a', ' ']:
            glyph = font.get_glyph(c)
            if glyph is None:
                results.append(("Gate 2: ASCII Glyphs", FAIL))
                return False
        results.append(("Gate 2: ASCII Glyphs", PASS))
        return True
    except Exception as e:
        results.append(("Gate 2: ASCII Glyphs", FAIL))
        return False


def gate3_chinese_glyphs():
    try:
        from tllos.virtual_machine.fonts.tll_font import TLLFont
        font = TLLFont()
        # Check common Chinese chars
        for c in ['智', '能', '系', '统', '状', '态']:
            glyph = font.get_glyph(c)
            if glyph is None:
                results.append(("Gate 3: Chinese Glyphs", FAIL))
                return False
        results.append(("Gate 3: Chinese Glyphs", PASS))
        return True
    except Exception as e:
        results.append(("Gate 3: Chinese Glyphs", FAIL))
        return False


def gate4_no_external_font():
    """Check no PIL font or Windows font file dependency."""
    try:
        # Check text_renderer.py
        fpath = VM_DIR / "text_renderer.py"
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should NOT use PIL ImageFont
        if 'ImageFont' in content or 'truetype' in content:
            results.append(("Gate 4: No External Font", FAIL))
            return False

        # Should NOT reference msyh.ttc or other Windows fonts
        if 'msyh' in content or 'simhei' in content or '.ttf' in content or '.ttc' in content:
            results.append(("Gate 4: No External Font", FAIL))
            return False

        results.append(("Gate 4: No External Font", PASS))
        return True
    except Exception as e:
        results.append(("Gate 4: No External Font", f"FAIL: {e}"))
        return False


def gate5_desktop_native_font():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLDesktopSurface
        fb = TLLFramebuffer(800, 600)
        surface = TLLDesktopSurface(fb)
        result = surface.render_desktop()
        if result["hash"] and surface.text_renderer.font_name == "TLL-Builtin-1.0":
            results.append(("Gate 5: Desktop Native Font", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 5: Desktop Native Font", FAIL))
    return False


def main():
    print("=" * 60)
    print("TLL OS Native Font Runtime Validator")
    print("=" * 60)
    print()

    gate1_native_font()
    gate2_ascii_glyphs()
    gate3_chinese_glyphs()
    gate4_no_external_font()
    gate5_desktop_native_font()

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
