#!/usr/bin/env python3
"""Test TLL Native Window Manager."""

from pathlib import Path
from tllos.virtual_machine import TLLOSVirtualMachine, TLLFramebuffer, TLLWindowManager, TLLCompositor, TLLTextRenderer

# Test Window System
print("=== TLL Native Window Manager Test ===")
print()

# Create desktop
fb = TLLFramebuffer(1920, 1080)
wm = TLLWindowManager(fb)
compositor = TLLCompositor(wm)
tr = TLLTextRenderer(fb)

# Create multiple windows
print("=== Creating Windows ===")

# Window 1: Agent Console
win1 = wm.create_window("Agent 控制台", 50, 50, 500, 400)
win1.clear(40, 50, 65)
win1.draw_border(100, 200, 255, 2)
tr.draw_text(70, 70, "Agent Console", 100, 200, 255, "medium")
print(f"  Window 1: {win1.id} '{win1.title}' {win1.width}x{win1.height}")

# Window 2: Task Space
win2 = wm.create_window("任务空间", 600, 100, 600, 500)
win2.clear(50, 65, 50)
win2.draw_border(100, 255, 150, 2)
tr.draw_text(620, 120, "Task Space", 100, 255, 150, "medium")
print(f"  Window 2: {win2.id} '{win2.title}' {win2.width}x{win2.height}")

# Window 3: Status Panel
win3 = wm.create_window("状态面板", 100, 500, 350, 200)
win3.clear(65, 50, 40)
win3.draw_border(255, 200, 100, 2)
tr.draw_text(120, 520, "Status Panel", 255, 200, 100, "medium")
print(f"  Window 3: {win3.id} '{win3.title}' {win3.width}x{win3.height}")

print()
print(f"Total windows: {wm.get_window_count()}")
print(f"Focused: {wm.focused_window.title if wm.focused_window else 'None'}")

# Composite
print()
print("=== Compositing ===")
result = compositor.composite()
print(f"Frame: {result['frame']}")
print(f"Resolution: {result['resolution']}")
print(f"Hash: {result['hash']}")
print(f"Windows composited: {result['windows']}")

# Test window operations
print()
print("=== Window Operations ===")
wm.move_window(win1.id, 100, 80)
print(f"Moved {win1.id} to (100, 80)")
wm.resize_window(win2.id, 700, 550)
print(f"Resized {win2.id} to 700x550")
wm.focus_window(win1)
print(f"Focused {win1.id} (z-index: {win1.z_index})")

# Re-composite
result2 = compositor.composite()
print(f"Re-composited frame: {result2['frame']}")
print(f"New hash: {result2['hash']}")

# Export screenshot
from tllos.virtual_machine import TLLDesktopSurface
surface = TLLDesktopSurface(fb)
output = Path("tll_multi_window.png")
ss = surface.export_screenshot(output)

print()
print("=== Screenshot Export ===")
print(f"Path: {ss.get('path')}")
print(f"Size: {ss.get('width')}x{ss.get('height')}")

if output.exists():
    size = output.stat().st_size
    print(f"File size: {size} bytes")
    print()
    print("PASS: TLL Native Window Manager works")
else:
    print("FAIL: Screenshot not exported")
