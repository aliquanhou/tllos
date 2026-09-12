#!/usr/bin/env python3
"""Test TLL Agent Boot & LLM Genesis."""

from tllos.virtual_machine import TLLAgent

print("=== TLL OS Agent Boot Test ===")
print()

# Boot Agent
agent = TLLAgent()
result = agent.boot()

print("=== Boot Result ===")
print(f"Agent ID: {result['agent_id']}")
print(f"State: {result['state']}")
print(f"Boot time: {result['boot_time_s']}s")
print()

print("=== LLM Bridge ===")
llm = result['llm']
print(f"Provider: {llm['provider']}")
print(f"Model: {llm['model']}")
print(f"Connected: {llm['connected']}")
print(f"Requests: {llm['requests']}")
print()

print("=== Capabilities ===")
caps = result['capabilities']
print(f"Total tools: {caps['total_tools']}")
print(f"Categories: {caps['categories']}")
print()

print("=== Boot Steps ===")
for step in result['boot_steps']:
    print(f"  Step {step['step']}: {step['name']} [{step['status']}]")

print()
print("=== Agent Goal Test ===")
goal_result = agent.receive_goal("创建一个商城系统")
print(f"Goal: {goal_result['goal']}")
print(f"Thought: {goal_result['thought']}")
print(f"State: {goal_result['state']}")
print(f"Plan steps: {len(goal_result['plan']['steps'])}")

print()
print("=== Execute Plan Test ===")
exec_result = agent.execute_plan()
print(f"Goal: {exec_result['goal']}")
print(f"Results: {len(exec_result['results'])} actions")
print(f"State: {exec_result['state']}")

print()
print("=== Agent Status ===")
status = agent.get_status()
print(f"State: {status['state']}")
print(f"Tools: {status['tool_count']}")
print(f"Tasks: {status['task_history']}")
print(f"Current goal: {status['current_goal']}")

print()
print("PASS: TLL Agent Boot & LLM Genesis works")
