#!/usr/bin/env python3
"""
TLL OS Agent Real Capability Binding Validator

5 Gates:
  Gate 1: Tool Runtime
  Gate 2: Agent Memory
  Gate 3: Agent Vision
  Gate 4: Real Tool Execution
  Gate 5: Agent Integration
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_tool_runtime():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
        from tllos.virtual_machine.agent import TLLToolRuntime
        fb = TLLFramebuffer(800, 600)
        wm = TLLWindowManager(fb)
        comp = TLLCompositor(wm)
        runtime = TLLToolRuntime(wm, comp)
        if len(runtime.tool_handlers) >= 10:
            results.append(("Gate 1: Tool Runtime", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Tool Runtime", FAIL))
    return False


def gate2_agent_memory():
    try:
        from tllos.virtual_machine.agent import TLLAgentMemory
        mem = TLLAgentMemory()
        mem.remember("test short", "short_term")
        mem.remember("test long", "long_term")
        mem.remember("test skill", "skill")
        status = mem.get_status()
        if status["short_term_count"] == 1 and status["long_term_count"] == 1 and status["skill_count"] == 1:
            results.append(("Gate 2: Agent Memory", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Agent Memory", FAIL))
    return False


def gate3_agent_vision():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
        from tllos.virtual_machine.agent import TLLAgentVision
        fb = TLLFramebuffer(800, 600)
        wm = TLLWindowManager(fb)
        comp = TLLCompositor(wm)
        vision = TLLAgentVision(wm, comp)
        obs = vision.observe_world()
        if obs["state"] == "OBSERVED" and "desktop" in obs:
            results.append(("Gate 3: Agent Vision", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Agent Vision", FAIL))
    return False


def gate4_real_tool_execution():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
        from tllos.virtual_machine.agent import TLLToolRuntime
        fb = TLLFramebuffer(800, 600)
        wm = TLLWindowManager(fb)
        comp = TLLCompositor(wm)
        runtime = TLLToolRuntime(wm, comp)

        # Real execution: create window
        result = runtime.execute_tool("display.create_window", title="Test", x=10, y=10, width=100, height=100)
        if result.success and result.output["window_id"]:
            # Verify window was actually created
            if len(wm.windows) == 1:
                results.append(("Gate 4: Real Tool Execution", PASS))
                return True
    except Exception as e:
        pass
    results.append(("Gate 4: Real Tool Execution", FAIL))
    return False


def gate5_agent_integration():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
        from tllos.virtual_machine.agent import TLLAgent, TLLToolRuntime, TLLAgentVision
        fb = TLLFramebuffer(800, 600)
        wm = TLLWindowManager(fb)
        comp = TLLCompositor(wm)

        agent = TLLAgent()
        agent.boot()
        agent.tool_runtime = TLLToolRuntime(wm, comp)
        agent.vision = TLLAgentVision(wm, comp)

        # Process goal
        goal_result = agent.receive_goal("test goal")
        exec_result = agent.execute_plan()

        if goal_result["state"] == "PLANNED" and exec_result["state"] == "EXECUTED":
            results.append(("Gate 5: Agent Integration", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 5: Agent Integration", FAIL))
    return False


def main():
    print("=" * 60)
    print("TLL OS Agent Real Capability Binding Validator")
    print("=" * 60)
    print()

    gate1_tool_runtime()
    gate2_agent_memory()
    gate3_agent_vision()
    gate4_real_tool_execution()
    gate5_agent_integration()

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
