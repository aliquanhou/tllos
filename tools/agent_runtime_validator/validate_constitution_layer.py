#!/usr/bin/env python3
"""
TLL OS Agent Constitution & Survival Layer Validator

5 Gates:
  Gate 1: Agent Self State
  Gate 2: Action Risk Evaluation
  Gate 3: Recovery Capability
  Gate 4: Agent Spawn Protocol
  Gate 5: Constitution Integration
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_agent_self():
    try:
        from tllos.virtual_machine.agent import TLLAgentSelf
        self_state = TLLAgentSelf("test-agent")
        self_state.update_health(energy=80.0, risk_level="LOW")
        self_state.record_error()
        self_state.record_recovery()
        health = self_state.get_health_summary()
        if health["energy"] == 85.0 and health["survival"] == "ALIVE":
            results.append(("Gate 1: Agent Self State", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Agent Self State", FAIL))
    return False


def gate2_risk_eval():
    try:
        from tllos.virtual_machine.agent import TLLActionRiskEvaluator
        evaluator = TLLActionRiskEvaluator()

        low = evaluator.evaluate_action("display.screenshot")
        high = evaluator.evaluate_action("process.stop")
        critical = evaluator.evaluate_action("system.shutdown")

        if (low.risk_level == "LOW" and
            high.risk_level == "HIGH" and
            critical.risk_level == "CRITICAL" and
            high.requires_approval and critical.requires_approval):
            results.append(("Gate 2: Action Risk Evaluation", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Action Risk Evaluation", FAIL))
    return False


def gate3_recovery():
    try:
        from tllos.virtual_machine.agent import TLLRecoveryManager
        recovery = TLLRecoveryManager()
        ckpt = recovery.create_checkpoint("test", {"state": "test"})
        result = recovery.restore_checkpoint(ckpt.checkpoint_id)
        if result["success"] and result["checkpoint_id"] == ckpt.checkpoint_id:
            results.append(("Gate 3: Recovery Capability", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Recovery Capability", FAIL))
    return False


def gate4_spawn():
    try:
        from tllos.virtual_machine.agent import TLLAgentSpawner
        from tllos.virtual_machine.agent.agent_spawner import AgentRecord
        spawner = TLLAgentSpawner()
        root = AgentRecord(agent_id="root", name="Root")
        spawner.agents["root"] = root

        child = spawner.spawn_agent("root", "Child Agent")
        grandchild = spawner.spawn_agent(child["agent_id"], "Grandchild")

        hierarchy = spawner.get_hierarchy()
        if hierarchy["total_agents"] == 3 and len(root.child_ids) == 1:
            results.append(("Gate 4: Agent Spawn Protocol", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Agent Spawn Protocol", FAIL))
    return False


def gate5_integration():
    """Test all components work together."""
    try:
        from tllos.virtual_machine.agent import (
            TLLAgentSelf, TLLActionRiskEvaluator,
            TLLRecoveryManager, TLLAgentSpawner
        )
        from tllos.virtual_machine.agent.agent_spawner import AgentRecord

        # Create all components
        self_state = TLLAgentSelf("integrated-agent")
        evaluator = TLLActionRiskEvaluator()
        recovery = TLLRecoveryManager()
        spawner = TLLAgentSpawner()

        # Simulate a risky action
        assessment = evaluator.evaluate_action("process.stop")

        # Create checkpoint before action
        recovery.create_checkpoint("Before risky action")

        # Action fails
        self_state.record_error()

        # Rollback
        recovery.rollback_to_latest()
        self_state.record_recovery()

        # Spawn a recovery agent
        root = AgentRecord(agent_id="integrated-agent", name="Root")
        spawner.agents["integrated-agent"] = root
        helper = spawner.spawn_agent("integrated-agent", "Recovery Helper")

        health = self_state.get_health_summary()
        if health["errors"] == 1 and health["recoveries"] == 1:
            results.append(("Gate 5: Constitution Integration", PASS))
            return True
    except Exception as e:
        results.append(("Gate 5: Constitution Integration", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Agent Constitution & Survival Layer Validator")
    print("=" * 60)
    print()

    gate1_agent_self()
    gate2_risk_eval()
    gate3_recovery()
    gate4_spawn()
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
