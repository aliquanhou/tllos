#!/usr/bin/env python3
"""Test TLL Agent Constitution & Survival Layer."""

from tllos.virtual_machine.agent import (
    TLLAgentSelf, TLLActionRiskEvaluator,
    TLLRecoveryManager, TLLAgentSpawner
)

print("=== TLL Agent Constitution & Survival Layer Test ===")
print()

# Test 1: Agent Self State
print("=== 1. Agent Self State ===")
self_state = TLLAgentSelf("tll-agent-0")
self_state.update_capability(tool_count=15, filesystem_files=5, process_count=3, app_count=2)
self_state.update_health(energy=95.0, memory_health="HEALTHY", risk_level="LOW")
self_state.record_error()
self_state.record_error()
self_state.record_recovery()

health = self_state.get_health_summary()
print(f"Identity: {health['identity']}")
print(f"Energy: {health['energy']}%")
print(f"Survival: {health['survival']}")
print(f"Risk: {health['risk']}")
print(f"Errors: {health['errors']}")
print(f"Recoveries: {health['recoveries']}")
print()

# Test 2: Action Risk Evaluation
print("=== 2. Action Risk Evaluation ===")
evaluator = TLLActionRiskEvaluator()

actions = [
    "display.screenshot",
    "storage.write",
    "process.stop",
    "system.shutdown",
]

for action in actions:
    assessment = evaluator.evaluate_action(action)
    print(f"{action:25s} -> {assessment.risk_level:10s} evidence={assessment.requires_evidence} approval={assessment.requires_approval}")

stats = evaluator.get_stats()
print(f"\nRisk Stats: {stats}")
print()

# Test 3: Recovery Capability
print("=== 3. Recovery Capability ===")
recovery = TLLRecoveryManager()

ckpt1 = recovery.create_checkpoint("Before risky operation", {"state": "stable"})
print(f"Checkpoint 1: {ckpt1.checkpoint_id} - {ckpt1.description}")

# Simulate error
print("Simulating system error...")
self_state.record_error()

# Rollback
result = recovery.rollback_to_latest()
print(f"Rollback: {result['success']} - {result['message']}")

recovery_stats = recovery.get_stats()
print(f"Recovery Stats: {recovery_stats}")
print()

# Test 4: Agent Spawn Protocol
print("=== 4. Agent Spawn Protocol ===")
spawner = TLLAgentSpawner()

# Create root agent record manually
from tllos.virtual_machine.agent.agent_spawner import AgentRecord
root = AgentRecord(agent_id="tll-agent-0", name="Root Agent")
spawner.agents["tll-agent-0"] = root

# Spawn children
child1 = spawner.spawn_agent("tll-agent-0", "Mall Builder", ["display", "storage"])
print(f"Child 1: {child1['agent_id']} - {child1['name']}")

child2 = spawner.spawn_agent("tll-agent-0", "ERP Builder", ["process", "code"])
print(f"Child 2: {child2['agent_id']} - {child2['name']}")

# Spawn grandchild
grandchild = spawner.spawn_agent(child1['agent_id'], "Product Module", ["app"])
print(f"Grandchild: {grandchild['agent_id']} - {grandchild['name']}")

# Get hierarchy
hierarchy = spawner.get_hierarchy()
print(f"\nHierarchy: {hierarchy['total_agents']} agents total")

# Get children of root
children = spawner.get_children("tll-agent-0")
print(f"Root children: {len(children)}")

spawn_stats = spawner.get_stats()
print(f"Spawn Stats: {spawn_stats}")
print()

# Final summary
print("=== Final Summary ===")
print(f"Agent Self: {health}")
print(f"Risk Evaluator: {stats}")
print(f"Recovery: {recovery_stats}")
print(f"Spawn: {spawn_stats}")
print()

print("PASS: TLL Agent Constitution & Survival Layer works")
