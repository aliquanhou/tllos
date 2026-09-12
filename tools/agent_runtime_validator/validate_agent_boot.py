#!/usr/bin/env python3
"""
TLL OS Agent Boot & LLM Genesis Validator

5 Gates:
  Gate 1: Agent Boot
  Gate 2: Tool Registry
  Gate 3: LLM Bridge
  Gate 4: Goal Processing
  Gate 5: No External Dependency
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

AGENT_DIR = PROJECT_ROOT / "tllos" / "virtual_machine" / "agent"

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_agent_boot():
    try:
        from tllos.virtual_machine.agent import TLLAgent
        agent = TLLAgent()
        result = agent.boot()
        if result["state"] == "ONLINE" and result["agent_id"] == "tll-agent-0":
            results.append(("Gate 1: Agent Boot", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Agent Boot", FAIL))
    return False


def gate2_tool_registry():
    try:
        from tllos.virtual_machine.agent import TLLToolRegistry
        registry = TLLToolRegistry()
        caps = registry.get_capabilities_summary()
        if caps["total_tools"] >= 10 and "display" in caps["categories"]:
            results.append(("Gate 2: Tool Registry", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Tool Registry", FAIL))
    return False


def gate3_llm_bridge():
    try:
        from tllos.virtual_machine.agent import TLLLLMBridge
        bridge = TLLLLMBridge()
        connect_result = bridge.connect()
        status = bridge.get_status()
        if status["connected"] and status["provider"] == "mock":
            results.append(("Gate 3: LLM Bridge", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: LLM Bridge", FAIL))
    return False


def gate4_goal_processing():
    try:
        from tllos.virtual_machine.agent import TLLAgent
        agent = TLLAgent()
        agent.boot()
        result = agent.receive_goal("测试目标")
        if result["state"] == "PLANNED" and len(result["plan"]["steps"]) >= 3:
            results.append(("Gate 4: Goal Processing", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Goal Processing", FAIL))
    return False


def gate5_no_external_dep():
    """Check no external LLM API dependency."""
    try:
        for pyfile in AGENT_DIR.glob("*.py"):
            with open(pyfile, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'openai' in content.lower() or 'anthropic' in content.lower():
                results.append(("Gate 5: No External LLM Dep", FAIL))
                return False
        results.append(("Gate 5: No External LLM Dep", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: No External LLM Dep", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Agent Boot & LLM Genesis Validator")
    print("=" * 60)
    print()

    gate1_agent_boot()
    gate2_tool_registry()
    gate3_llm_bridge()
    gate4_goal_processing()
    gate5_no_external_dep()

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
