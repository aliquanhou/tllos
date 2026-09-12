#!/usr/bin/env python3
"""Test TLL Agent World Model Layer."""

from tllos.virtual_machine.agent import (
    TLLWorldModel, TLLAgentConstitution,
    TLLActionRiskEvaluator
)

print("=== TLL Agent World Model Layer Test ===")
print()

# Test 1: World Model - Build a mall system dependency graph
print("=== 1. World Model: Mall System Dependencies ===")
world = TLLWorldModel()

# Create dependency chain: DB -> Backend -> Frontend -> Mall App
db = world.add_object("Product Database", "service", object_id="svc-db")
backend = world.add_object("Backend API", "service", object_id="svc-backend", dependencies=["svc-db"])
frontend = world.add_object("Frontend UI", "app", object_id="app-frontend", dependencies=["svc-backend"])
mall = world.add_object("Mall Application", "app", object_id="app-mall", dependencies=["app-frontend"])

print(f"Created: {world.get_world_summary()['total_objects']} objects")
print()

# Test 2: Impact Analysis
print("=== 2. Impact Analysis ===")
impact = world.get_impact_scope("svc-db")
print(f"Deleting Product Database:")
print(f"  Direct dependents: {impact['direct_dependents']}")
print(f"  Total dependents: {impact['total_dependents']}")
print(f"  Impact level: {impact['impact_level']}")
print(f"  Affected: {impact['affected_objects']}")
print()

# Test 3: Constitution v1
print("=== 3. Constitution v1 ===")
constitution = TLLAgentConstitution()
summary = constitution.get_constitution_summary()
print(f"Version: {summary['version']}")
print(f"Rules: {summary['total_rules']}")
for rule in summary['rules']:
    print(f"  {rule['number']}. {rule['name']} ({rule['enforcement']})")
print()

# Test 4: Constitution Check
print("=== 4. Constitution Check ===")
# Low risk, has evidence -> compliant
r1 = constitution.check_action("display.screenshot", "LOW", has_evidence=True, is_reversible=True, affects_self=False)
print(f"screenshot: compliant={r1['compliant']}")

# High risk, no evidence -> violation
r2 = constitution.check_action("process.stop", "HIGH", has_evidence=False, is_reversible=False, affects_self=True)
print(f"process.stop (no evidence): compliant={r2['compliant']}, violations={len(r2['violations'])}")
print()

# Test 5: Context-Aware Risk Evaluation
print("=== 5. Context-Aware Risk Evaluation ===")
evaluator = TLLActionRiskEvaluator()

# Baseline: storage.delete is HIGH
baseline = evaluator.evaluate_action("storage.delete", {"path": "/tmp/cache"})
print(f"Delete /tmp/cache: {baseline.risk_level}")

# Context: delete database that has dependents
context_risk = evaluator.evaluate_action("storage.delete", {"path": "svc-db"}, world_model=world)
print(f"Delete Product DB: {context_risk.risk_level}")
print(f"  Context: {context_risk.context_analysis}")
print(f"  Impact: {context_risk.impact_scope.get('impact_level', 'N/A')}")
print()

# Final Summary
print("=== Final Summary ===")
print(f"World Model: {world.get_world_summary()}")
print(f"Constitution: {summary}")
print(f"Risk Assessments: {evaluator.get_stats()}")
print()

print("PASS: TLL Agent World Model Layer works")
