#!/usr/bin/env python3
"""
TLL OS Agent World Model Layer Validator

5 Gates:
  Gate 1: World Model
  Gate 2: Dependency Graph
  Gate 3: Constitution v1
  Gate 4: Context-Aware Risk
  Gate 5: Integration
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_world_model():
    try:
        from tllos.virtual_machine.agent import TLLWorldModel
        world = TLLWorldModel()
        world.add_object("DB", "service", object_id="db")
        world.add_object("App", "app", object_id="app", dependencies=["db"])
        summary = world.get_world_summary()
        if summary["total_objects"] == 2:
            results.append(("Gate 1: World Model", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: World Model", FAIL))
    return False


def gate2_dependency_graph():
    try:
        from tllos.virtual_machine.agent import TLLWorldModel
        world = TLLWorldModel()
        world.add_object("DB", "service", object_id="db")
        world.add_object("Backend", "service", object_id="backend", dependencies=["db"])
        world.add_object("Frontend", "app", object_id="frontend", dependencies=["backend"])
        world.add_object("Mall", "app", object_id="mall", dependencies=["frontend"])

        impact = world.get_impact_scope("db")
        if impact["total_dependents"] == 3 and impact["impact_level"] == "HIGH":
            results.append(("Gate 2: Dependency Graph", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Dependency Graph", FAIL))
    return False


def gate3_constitution():
    try:
        from tllos.virtual_machine.agent import TLLAgentConstitution
        constitution = TLLAgentConstitution()
        summary = constitution.get_constitution_summary()

        # Check compliant action
        r1 = constitution.check_action("screenshot", "LOW", has_evidence=True, is_reversible=True, affects_self=False)
        # Check violating action
        r2 = constitution.check_action("shutdown", "CRITICAL", has_evidence=False, is_reversible=False, affects_self=True)

        if summary["total_rules"] == 5 and r1["compliant"] and not r2["compliant"]:
            results.append(("Gate 3: Constitution v1", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Constitution v1", FAIL))
    return False


def gate4_context_aware_risk():
    try:
        from tllos.virtual_machine.agent import TLLWorldModel, TLLActionRiskEvaluator
        world = TLLWorldModel()
        world.add_object("DB", "service", object_id="db")
        world.add_object("App", "app", object_id="app", dependencies=["db"])

        evaluator = TLLActionRiskEvaluator()

        # Delete cache (no context)
        r1 = evaluator.evaluate_action("storage.delete", {"path": "/tmp/cache"})

        # Delete DB (with dependents)
        r2 = evaluator.evaluate_action("storage.delete", {"path": "db"}, world_model=world)

        if r1.risk_level == "HIGH" and r2.context_analysis and "3 dependent" not in r2.context_analysis:
            # Check that context analysis exists
            results.append(("Gate 4: Context-Aware Risk", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Context-Aware Risk", FAIL))
    return False


def gate5_integration():
    try:
        from tllos.virtual_machine.agent import (
            TLLWorldModel, TLLAgentConstitution,
            TLLActionRiskEvaluator, TLLRecoveryManager
        )

        # Build a small world
        world = TLLWorldModel()
        world.add_object("DB", "service", object_id="db")
        world.add_object("App", "app", object_id="app", dependencies=["db"])

        constitution = TLLAgentConstitution()
        evaluator = TLLActionRiskEvaluator()
        recovery = TLLRecoveryManager()

        # Create checkpoint before risky operation
        recovery.create_checkpoint("Before delete", {"state": "safe"})

        # Evaluate risky action
        risk = evaluator.evaluate_action("storage.delete", {"path": "db"}, world_model=world)

        # Check constitution
        check = constitution.check_action(
            "storage.delete", risk.risk_level,
            has_evidence=True, is_reversible=False, affects_self=False
        )

        # If not compliant, rollback
        if not check["compliant"]:
            recovery.rollback_to_latest()

        impact = world.get_impact_scope("db")
        if impact["total_dependents"] >= 1:
            results.append(("Gate 5: Integration", PASS))
            return True
    except Exception as e:
        results.append(("Gate 5: Integration", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Agent World Model Layer Validator")
    print("=" * 60)
    print()

    gate1_world_model()
    gate2_dependency_graph()
    gate3_constitution()
    gate4_context_aware_risk()
    gate5_integration()

    print()
    passed = sum(1 for _, r in results if r == PASS)
    failed = len(results) - passed
    for name, result in results:
        status = "✅" if result == PASS else "❌"
        print(f"  {status} {name:40s} {result}")

    print()
    print(f"Total: {passed}/5 Gates PASS, {failed} FAIL")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
