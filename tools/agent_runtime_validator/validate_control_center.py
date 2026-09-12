#!/usr/bin/env python3
"""
TLL OS Reality Control Center Validator

5 Gates:
  Gate 1: Agent Live Loop (observe→understand→decide→risk→execute→remember)
  Gate 2: Command Loop (input → agent cycle)
  Gate 3: Risk Check (real risk evaluator)
  Gate 4: Boot Identity (TLL OS Agent identity)
  Gate 5: Screenshot + Status
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_live_loop():
    try:
        from tllos.virtual_machine.agent import (
            TLLAgentSelf, TLLWorldModel, TLLExperienceMemory,
            TLLToolRuntime, TLLAppRuntime, TLLActionRiskEvaluator,
            TLLAgentLiveLoop
        )
        from tllos.virtual_machine import TLLFramebuffer

        fb = TLLFramebuffer(800, 600)
        agent = TLLAgentSelf("test")
        world = TLLWorldModel()
        exp = TLLExperienceMemory()
        tool_rt = TLLToolRuntime(fb, None)
        app_rt = TLLAppRuntime(fb, None)
        risk = TLLActionRiskEvaluator()

        loop = TLLAgentLiveLoop(agent, world, exp, tool_rt, app_rt, risk)
        result = loop.run_cycle(goal="test goal")

        if (result["loop"] == 1 and
            result["goal"] == "test goal" and
            len(result["plan"]) >= 1):
            results.append(("Gate 1: Agent Live Loop", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Agent Live Loop", FAIL))
    return False


def gate2_command_loop():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLControlCenterDesktop
        from tllos.virtual_machine.agent import (
            TLLAgentSelf, TLLWorldModel, TLLExperienceMemory,
            TLLActionRiskEvaluator, TLLAgentLiveLoop
        )

        fb = TLLFramebuffer(800, 600)
        agent = TLLAgentSelf("test")
        world = TLLWorldModel()
        exp = TLLExperienceMemory()
        risk = TLLActionRiskEvaluator()
        loop = TLLAgentLiveLoop(agent, world, exp, None, None, risk)

        desktop = TLLControlCenterDesktop(
            framebuffer=fb, agent_self=agent, world_model=world,
            experience=exp, live_loop=loop
        )

        result = desktop.submit_command("build a mall")
        if result["goal"] == "build a mall" and len(result["plan"]) >= 2:
            results.append(("Gate 2: Command Loop", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Command Loop", FAIL))
    return False


def gate3_risk_check():
    try:
        from tllos.virtual_machine.agent import (
            TLLActionRiskEvaluator, TLLWorldModel
        )

        risk = TLLActionRiskEvaluator()
        world = TLLWorldModel()

        # Low risk action
        r1 = risk.evaluate_action("storage.read", world_model=world)
        # High risk action
        r2 = risk.evaluate_action("storage.delete", world_model=world)

        if (r1.risk_level == "LOW" and
            r2.risk_level == "HIGH"):
            results.append(("Gate 3: Risk Check", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Risk Check", FAIL))
    return False


def gate4_boot_identity():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLControlCenterDesktop

        fb = TLLFramebuffer(800, 600)
        desktop = TLLControlCenterDesktop(framebuffer=fb)
        desktop.render()

        status = desktop.get_status_text()
        if "TLL OS CONTROL CENTER" in status and "Agent" in status:
            results.append(("Gate 4: Boot Identity", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Boot Identity", FAIL))
    return False


def gate5_screenshot_status():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLControlCenterDesktop

        fb = TLLFramebuffer(800, 600)
        desktop = TLLControlCenterDesktop(framebuffer=fb)

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            ss = desktop.take_screenshot(tmp.name)
            if not ss["saved"]:
                results.append(("Gate 5: Screenshot + Status", FAIL))
                return False

        status = desktop.get_status_text()
        if "Frame:" not in status:
            results.append(("Gate 5: Screenshot + Status", FAIL))
            return False

        results.append(("Gate 5: Screenshot + Status", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: Screenshot + Status", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Reality Control Center Validator")
    print("=" * 60)
    print()

    gate1_live_loop()
    gate2_command_loop()
    gate3_risk_check()
    gate4_boot_identity()
    gate5_screenshot_status()

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
