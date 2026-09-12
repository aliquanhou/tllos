#!/usr/bin/env python3
"""Test TLL OS Virtual Display Reality."""

from pathlib import Path
from tllos.virtual_machine import TLLOSVirtualMachine

# Boot TLL OS with new display
vm = TLLOSVirtualMachine()
result = vm.boot()

print("=== TLL OS Virtual Display Reality ===")
print(f"OS: {result['os']}")
print(f"State: {result['state']}")
print()
print("=== Desktop Surface ===")
d = result['desktop']
print(f"Frame: {d['frame']}")
print(f"Resolution: {d['resolution']}")
print(f"Hash: {d['hash']}")
print()

# Export screenshot
output = Path("tll_desktop_preview.png")
ss = vm.desktop_surface.export_screenshot(output)
print("=== Screenshot Export ===")
print(f"Path: {ss.get('path')}")
print(f"Size: {ss.get('width')}x{ss.get('height')}")
print(f"Format: {ss.get('format')}")
print(f"Hash: {ss.get('hash')}")
print()

if output.exists():
    size = output.stat().st_size
    print(f"File size: {size} bytes")
    print("PASS: TLL Desktop Surface renders and exports PNG")
else:
    print("FAIL: Screenshot not exported")
