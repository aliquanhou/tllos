#!/usr/bin/env python3
"""Test TLL Text Rendering Engine."""

from pathlib import Path
from tllos.virtual_machine import TLLOSVirtualMachine

# Boot TLL OS with text rendering
vm = TLLOSVirtualMachine()
result = vm.boot()

print("=== TLL OS Text Rendering Engine ===")
print(f"OS: {result['os']}")
print(f"State: {result['state']}")
print()
print("=== Desktop Surface ===")
d = result['desktop']
print(f"Frame: {d['frame']}")
print(f"Resolution: {d['resolution']}")
print(f"Hash: {d['hash']}")
print()

# Test text rendering directly
fb = vm.framebuffer
tr = vm.desktop_surface.text_renderer

print("=== Text Renderer Test ===")
print(f"Font path: {tr.font_path}")
print()

# Test English
t1 = tr.draw_text(100, 400, "Hello TLL OS", 255, 255, 255, "medium")
print(f"English: '{t1['text']}' {t1['width']}x{t1['height']} hash={t1['hash']}")

# Test Chinese
t2 = tr.draw_text(100, 430, "TLL OS 智能代理", 100, 200, 255, "large")
print(f"Chinese: '{t2['text']}' {t2['width']}x{t2['height']} hash={t2['hash']}")

t3 = tr.draw_text(100, 470, "系统状态: ONLINE", 100, 255, 150, "small")
print(f"Chinese2: '{t3['text']}' {t3['width']}x{t3['height']} hash={t3['hash']}")

# Re-render desktop with text
result2 = vm.desktop_surface.render_desktop()
print()
print(f"Re-rendered frame: {result2['frame']}")
print(f"New hash: {result2['hash']}")

# Export screenshot
output = Path("tll_desktop_text.png")
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
    print("PASS: TLL Text Rendering Engine works")
else:
    print("FAIL: Screenshot not exported")
