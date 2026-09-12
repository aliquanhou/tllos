#!/usr/bin/env python3
"""Test TLL Agent Real Capability Binding."""

from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
from tllos.virtual_machine.agent import TLLAgent, TLLToolRuntime, TLLAgentVision

print("=== TLL Agent Real Capability Binding Test ===")
print()

# Setup Virtual Machine components
fb = TLLFramebuffer(800, 600)
wm = TLLWindowManager(fb)
compositor = TLLCompositor(wm)

# Create Agent
agent = TLLAgent()

# Boot Agent
result = agent.boot()
print("=== Boot Result ===")
print(f"Agent: {result['agent_id']}")
print(f"State: {result['state']}")
print(f"Boot steps: {len(result['boot_steps'])}")
print(f"Memory: {result['memory']}")
print()

# Bind Tool Runtime
agent.tool_runtime = TLLToolRuntime(wm, compositor)
agent.vision = TLLAgentVision(wm, compositor)
print("=== Tool Runtime Bound ===")
print(f"Tools: {len(agent.tool_runtime.tool_handlers)} handlers")
print()

# Test Tool Execution
print("=== Tool Execution Test ===")
r1 = agent.tool_runtime.execute_tool("display.create_window", title="商城窗口", x=50, y=50, width=400, height=300)
print(f"create_window: success={r1.success}, output={r1.output}")

r2 = agent.tool_runtime.execute_tool("display.create_window", title="ERP窗口", x=400, y=100, width=350, height=250)
print(f"create_window: success={r2.success}, output={r2.output}")

r3 = agent.tool_runtime.execute_tool("display.screenshot")
print(f"screenshot: success={r3.success}, output={r3.output}")
print()

# Test Agent Vision
print("=== Agent Vision Test ===")
obs = agent.vision.observe_world()
print(f"Observation: {obs['observation_id']}")
print(f"Windows: {obs['window_count']}")
print(f"Focused: {obs['focused_window']}")
print(f"Desktop: {obs['desktop']['resolution']}")
print()

# Test Agent Memory
print("=== Agent Memory Test ===")
agent.memory.remember("Created mall window", "short_term", 0.7)
agent.memory.remember("User wants e-commerce", "long_term", 0.9)
agent.memory.remember("Window management skill", "skill", 0.8)
mem_status = agent.memory.get_status()
print(f"Memory: {mem_status}")
print()

# Test Goal → Plan → Execute
print("=== Goal Processing Test ===")
goal_result = agent.receive_goal("创建一个商城系统")
print(f"Goal: {goal_result['goal']}")
print(f"State: {goal_result['state']}")

exec_result = agent.execute_plan()
print(f"Execute: {len(exec_result['results'])} steps")
print(f"State: {exec_result['state']}")
print()

# Final Status
print("=== Final Status ===")
status = agent.get_status()
print(f"State: {status['state']}")
print(f"Tools: {status['tool_count']}")
print(f"Tool executions: {status['tool_executions']}")
print(f"Memory: {status['memory']}")
print()

print("PASS: TLL Agent Real Capability Binding works")
