#!/usr/bin/env python3
"""
TLL OS Native Desktop Experience Validator

5 Gates:
  Gate 1: Desktop Theme Load
  Gate 2: Agent Home (real data binding)
  Gate 3: World Model (real data binding)
  Gate 4: Creation Gallery (real data binding)
  Gate 5: Screenshot + Status Text
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_desktop_theme():
    try:
        from tllos.virtual_machine.desktop import TLLTheme
        palette = TLLTheme.get_palette()
        if (palette["background"] == (5, 8, 18) and
            palette["primary"] == (0, 229, 255) and
            palette["alive"] == (0, 255, 136)):
            results.append(("Gate 1: Desktop Theme Load", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Desktop Theme Load", FAIL))
    return False


def gate2_agent_home():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLDesktopSurface
        from tllos.virtual_machine.agent import TLLAgentSelf

        fb = TLLFramebuffer(800, 600)
        agent = TLLAgentSelf("test-agent")
        agent.update_health(energy=90.0, risk_level="LOW")

        desktop = TLLDesktopSurface(framebuffer=fb, agent_self=agent)
        result = desktop.render()

        if result["panels_rendered"] >= 1 and result["frame_hash"] is not None:
            results.append(("Gate 2: Agent Home (real data)", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Agent Home (real data)", FAIL))
    return False


def gate3_world_model():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLDesktopSurface
        from tllos.virtual_machine.agent import TLLWorldModel

        fb = TLLFramebuffer(800, 600)
        world = TLLWorldModel()
        world.add_object("Test DB", "service", object_id="db")
        world.add_object("Test App", "app", object_id="app", dependencies=["db"])

        desktop = TLLDesktopSurface(framebuffer=fb, world_model=world)
        result = desktop.render()

        if result["panels_rendered"] >= 1:
            results.append(("Gate 3: World Model (real data)", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: World Model (real data)", FAIL))
    return False


def gate4_creation_gallery():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLDesktopSurface
        from tllos.virtual_machine.agent import TLLAppRuntime

        fb = TLLFramebuffer(800, 600)
        app_rt = TLLAppRuntime(None, None)
        app_rt.create_app("Test Mall")

        desktop = TLLDesktopSurface(framebuffer=fb, app_runtime=app_rt)
        result = desktop.render()

        if result["panels_rendered"] >= 1:
            results.append(("Gate 4: Creation Gallery (real data)", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Creation Gallery (real data)", FAIL))
    return False


def gate5_screenshot_and_status():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLDesktopSurface
        from tllos.virtual_machine.agent import TLLAgentSelf, TLLWorldModel, TLLExperienceMemory

        fb = TLLFramebuffer(800, 600)
        agent = TLLAgentSelf("test-agent")
        world = TLLWorldModel()
        exp = TLLExperienceMemory()
        exp.record_experience("test", "ev", {}, {}, "SUCCESS", "learned", "LOW")

        desktop = TLLDesktopSurface(
            framebuffer=fb,
            agent_self=agent,
            world_model=world,
            experience=exp
        )

        # Status text
        status = desktop.get_status_text()
        if "TLL OS Desktop Status" not in status:
            results.append(("Gate 5: Screenshot + Status", FAIL))
            return False

        # Screenshot
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            screenshot_result = desktop.take_screenshot(tmp.name)
            if not screenshot_result["saved"]:
                results.append(("Gate 5: Screenshot + Status", FAIL))
                return False

        results.append(("Gate 5: Screenshot + Status", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: Screenshot + Status", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Native Desktop Experience Validator")
    print("=" * 60)
    print()

    gate1_desktop_theme()
    gate2_agent_home()
    gate3_world_model()
    gate4_creation_gallery()
    gate5_screenshot_and_status()

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
