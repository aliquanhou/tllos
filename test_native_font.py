#!/usr/bin/env python3
"""Test TLL Native Font Runtime."""

from pathlib import Path
from tllos.virtual_machine import TLLOSVirtualMachine

# Boot TLL OS with native font
vm = TLLOSVirtualMachine()
result = vm.boot()

print("=== TLL OS Native Font Runtime ===")
print(f"OS: {result['os']}")
print(f"State: {result['state']}")
print()

# Test native font directly
fb = vm.framebuffer
tr = vm.desktop_surface.text_renderer

print("=== Native Font Test ===")
print(f"Font: {tr.font_name}")
print()

# Test English
t1 = tr.draw_text(100, 400, "Hello TLL OS", 255, 255, 255, "medium")
print(f"English: '{t1['text']}' {t1['width']}x{t1['height']} hash={t1['hash']}")

# Test Chinese
t2 = tr.draw_text(100, 430, "TLL OS 智能代理", 100, 200, 255, "large")
print(f"Chinese: '{t2['text']}' {t2['width']}x{t2['height']} hash={t2['hash']}")

t3 = tr.draw_text(100, 470, "系统状态: ONLINE", 100, 255, 150, "small")
print(f"Chinese2: '{t3['text']}' {t3['width']}x{t3['height']} hash={t3['hash']}")

# Re-render desktop
result2 = vm.desktop_surface.render_desktop()
print()
print(f"Re-rendered frame: {result2['frame']}")
print(f"Hash: {result2['hash']}")

# Export screenshot
output = Path("tll_desktop_native_font.png")
ss = vm.desktop_surface.export_screenshot(output)
print()
print("=== Screenshot Export ===")
print(f"Path: {ss.get('path')}")
print(f"Size: {ss.get('width')}x{ss.get('height')}")
print(f"Format: {ss.get('format')}")

if output.exists():
    size = output.stat().st_size
    print(f"File size: {size} bytes")
    print()
    print("PASS: TLL Native Font Runtime works")
else:
    print("FAIL: Screenshot not exported")
