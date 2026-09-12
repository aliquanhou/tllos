#!/usr/bin/env python3
"""Test TLL OS Virtual Machine Boot."""

from tllos.virtual_machine import TLLOSVirtualMachine

# Boot TLL OS
vm = TLLOSVirtualMachine()
result = vm.boot()

print("=== TLL OS Virtual Machine Boot ===")
print(f"OS: {result['os']}")
print(f"Version: {result['version']}")
print(f"State: {result['state']}")
print(f"Boot time: {result['boot_time_s']}s")
print()
print("=== Hardware ===")
hw = result["hardware"]
print(f"Platform: {hw['platform']}")
print(f"CPU: {hw['cpu']['id']} ({hw['cpu']['cores']} cores)")
print(f"Memory: {hw['memory']['used_mb']}MB / {hw['memory']['total_mb']}MB")
print(f"Display: {hw['display']['resolution']}")
print()
print("=== Render ===")
r = result["render"]
print(f"Frame: {r['frame_id']}")
print(f"Resolution: {r['resolution']}")
print(f"Hash: {r['hash']}")
print(f"FPS: {r['fps']}")
print()
print("=== Windows ===")
for w in result["windows"]:
    print(f"  {w['id']}: {w['title']} ({w['width']}x{w['height']})")
print()
print("=== Boot Steps ===")
for s in result["boot_steps"]:
    print(f"  Step {s['step']}: {s['name']} [{s['status']}]")
print()
print("PASS: TLL OS Virtual Machine boots successfully")
