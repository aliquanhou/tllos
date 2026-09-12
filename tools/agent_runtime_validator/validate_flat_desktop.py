#!/usr/bin/env python3
"""
TLL OS Flat Intelligence Desktop v1.0 Validator

5 Gates:
  Gate 1: Theme Load
  Gate 2: Runtime Data Binding
  Gate 3: Desktop Surface Render
  Gate 4: Owner Command
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


def gate1_theme_load():
    try:
        from tllos.virtual_machine.desktop import TLLFlatTheme
        palette = TLLFlatTheme.get_palette()
        if (palette["background"] == (5, 8, 18) and
            palette["primary"] == (0, 229, 255) and
            palette["creation"] == (255, 209, 102)):
            results.append(("Gate 1: Theme Load", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Theme Load", FAIL))
    return False


def gate2_runtime_binding():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLFlatDesktop
        from tllos.virtual_machine.agent import TLLAgentSelf, TLLWorldModel, TLLExperienceMemory

        fb = TLLFramebuffer(800, 600)
        agent = TLLAgentSelf("test")
        world = TLLWorldModel()
        world.add_object("Test", "service", object_id="t1")
        exp = TLLExperienceMemory()
        exp.record_experience("test", "ev", {}, {}, "SUCCESS", "learned", "LOW")

        desktop = TLLFlatDesktop(
            framebuffer=fb,
            agent_self=agent,
            world_model=world,
            experience=exp
        )
        result = desktop.render()

        # Verify runtime data is bound
        status = desktop.get_status_text()
        if "test" in status and "World Objects: 1" in status:
            results.append(("Gate 2: Runtime Data Binding", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Runtime Data Binding", FAIL))
    return False


def gate3_desktop_render():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLFlatDesktop

        fb = TLLFramebuffer(1280, 800)
        desktop = TLLFlatDesktop(framebuffer=fb)
        result = desktop.render()

        if result["panels_rendered"] >= 5 and result["frame_hash"] is not None:
            results.append(("Gate 3: Desktop Surface Render", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Desktop Surface Render", FAIL))
    return False


def gate4_owner_command():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLFlatDesktop

        fb = TLLFramebuffer(800, 600)
        desktop = TLLFlatDesktop(framebuffer=fb)

        result = desktop.submit_command("create a mall system")
        if result["status"] == "received" and "create a mall" in result["command"]:
            results.append(("Gate 4: Owner Command", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Owner Command", FAIL))
    return False


def gate5_screenshot_clipboard():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLFlatDesktop
        from tllos.virtual_machine.agent import TLLAgentSelf

        fb = TLLFramebuffer(800, 600)
        agent = TLLAgentSelf("test")
        desktop = TLLFlatDesktop(framebuffer=fb, agent_self=agent)

        # Screenshot
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            ss = desktop.take_screenshot(tmp.name)
            if not ss["saved"]:
                results.append(("Gate 5: Screenshot + Clipboard", FAIL))
                return False

        # Clipboard (status text)
        status = desktop.get_status_text()
        if "TLL OS STATUS REPORT" not in status:
            results.append(("Gate 5: Screenshot + Clipboard", FAIL))
            return False

        results.append(("Gate 5: Screenshot + Clipboard", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: Screenshot + Clipboard", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Flat Intelligence Desktop v1.0 Validator")
    print("=" * 60)
    print()

    gate1_theme_load()
    gate2_runtime_binding()
    gate3_desktop_render()
    gate4_owner_command()
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
