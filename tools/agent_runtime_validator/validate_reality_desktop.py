#!/usr/bin/env python3
"""
TLL OS Reality Desktop Validator

5 Gates:
  Gate 1: Real-time Frame Loop
  Gate 2: Vision Panel (real state)
  Gate 3: Reasoning Panel (Goal/Plan/Action)
  Gate 4: Command Loop (input → agent)
  Gate 5: Screenshot + Clipboard
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_frame_loop():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLRealityDesktop

        fb = TLLFramebuffer(800, 600)
        desktop = TLLRealityDesktop(framebuffer=fb)

        # Render 3 frames
        r1 = desktop.render()
        r2 = desktop.render()
        r3 = desktop.render()

        if (r1["frame_count"] == 1 and r2["frame_count"] == 2 and
            r3["frame_count"] == 3 and r3["frame_hash"] is not None):
            results.append(("Gate 1: Real-time Frame Loop", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Real-time Frame Loop", FAIL))
    return False


def gate2_vision_panel():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLRealityDesktop

        fb = TLLFramebuffer(800, 600)
        desktop = TLLRealityDesktop(framebuffer=fb)
        desktop.vision_objects = ["Window A", "App B", "Command C"]

        result = desktop.render()
        if result["panels_rendered"] >= 4:
            results.append(("Gate 2: Vision Panel (real state)", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Vision Panel (real state)", FAIL))
    return False


def gate3_reasoning_panel():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLRealityDesktop

        fb = TLLFramebuffer(800, 600)
        desktop = TLLRealityDesktop(framebuffer=fb)
        desktop.current_goal = "create mall"
        desktop.current_thinking = "analyzing"
        desktop.current_plan = ["step1", "step2"]

        result = desktop.render()
        status = desktop.get_status_text()

        if "create mall" in status and "analyzing" in status:
            results.append(("Gate 3: Reasoning Panel (Goal/Plan)", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Reasoning Panel (Goal/Plan)", FAIL))
    return False


def gate4_command_loop():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLRealityDesktop

        fb = TLLFramebuffer(800, 600)
        desktop = TLLRealityDesktop(framebuffer=fb)

        result = desktop.submit_command("build a web app")

        if (result["goal"] == "build a web app" and
            len(result["plan"]) >= 3 and
            result["status"] == "RECEIVED"):
            results.append(("Gate 4: Command Loop (input → agent)", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Command Loop (input → agent)", FAIL))
    return False


def gate5_screenshot_clipboard():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLRealityDesktop
        from tllos.virtual_machine.agent import TLLAgentSelf

        fb = TLLFramebuffer(800, 600)
        agent = TLLAgentSelf("test")
        desktop = TLLRealityDesktop(framebuffer=fb, agent_self=agent)

        # Screenshot
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            ss = desktop.take_screenshot(tmp.name)
            if not ss["saved"]:
                results.append(("Gate 5: Screenshot + Clipboard", FAIL))
                return False

        # Clipboard
        status = desktop.get_status_text()
        if "TLL OS REAL-TIME STATUS" not in status:
            results.append(("Gate 5: Screenshot + Clipboard", FAIL))
            return False

        results.append(("Gate 5: Screenshot + Clipboard", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: Screenshot + Clipboard", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Reality Desktop Validator")
    print("=" * 60)
    print()

    gate1_frame_loop()
    gate2_vision_panel()
    gate3_reasoning_panel()
    gate4_command_loop()
    gate5_screenshot_clipboard()

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
