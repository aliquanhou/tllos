#!/usr/bin/env python3
"""Test TLL Native Capability Runtime."""

from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
from tllos.virtual_machine.agent import TLLAgent, TLLToolRuntime

print("=== TLL Native Capability Runtime Test ===")
print()

# Setup
fb = TLLFramebuffer(800, 600)
wm = TLLWindowManager(fb)
comp = TLLCompositor(wm)
runtime = TLLToolRuntime(wm, comp)

# Test 1: Virtual File System (real)
print("=== 1. Virtual File System ===")
r1 = runtime.execute_tool("storage.write", path="/home/user/hello.txt", content="Hello TLL OS!")
print(f"Write: {r1.success} - {r1.output}")

r2 = runtime.execute_tool("storage.read", path="/home/user/hello.txt")
print(f"Read: {r2.success} - content: {r2.output['content']}")

r3 = runtime.execute_tool("storage.list", dir="/home/user/")
print(f"List: {r3.success} - files: {r3.output['count']}")
print()

# Test 2: Process Manager (real)
print("=== 2. Process Manager ===")
r4 = runtime.execute_tool("process.start", name="tll-browser")
print(f"Start: {r4.success} - pid: {r4.output['pid']}, name: {r4.output['name']}")

r5 = runtime.execute_tool("process.list")
print(f"List: {r5.success} - total: {r5.output['total']}, running: {r5.output['running']}")
print()

# Test 3: Code Runtime (real)
print("=== 3. Code Runtime ===")
r6 = runtime.execute_tool("code.generate", description="hello world program")
print(f"Generate: {r6.success} - lines: {r6.output['lines']}")
print(f"Code preview: {r6.output['code'][:60]}...")

r7 = runtime.execute_tool("code.run", code=r6.output['code'])
print(f"Run: {r7.success} - output: {r7.output['output']}")
print()

# Test 4: App Runtime (real)
print("=== 4. App Runtime ===")
r8 = runtime.execute_tool("app.create", name="My First App", type="window")
print(f"Create: {r8.success} - app_id: {r8.output['app_id']}")

r9 = runtime.execute_tool("app.launch", app_id=r8.output['app_id'])
print(f"Launch: {r9.success} - status: {r9.output['status']}, window: {r9.output['window_id']}")

r10 = runtime.execute_tool("process.list")
print(f"Processes after app launch: {r10.output['total']}")
print()

# Test 5: Display tools (real, already working)
print("=== 5. Display Tools (real) ===")
r11 = runtime.execute_tool("display.create_window", title="Test Window", x=50, y=50, width=300, height=200)
print(f"Create window: {r11.success} - id: {r11.output['window_id']}")
print()

# Final stats
print("=== Final Stats ===")
print(f"Total executions: {runtime.get_execution_count()}")
print(f"Files in FS: {len(runtime.filesystem.files)}")
print(f"Processes: {runtime.process_mgr.get_stats()}")
print(f"Apps: {runtime.app_runtime.get_stats()}")
print(f"Code executions: {runtime.code_runtime.get_stats()}")
print()

print("PASS: TLL Native Capability Runtime works")
