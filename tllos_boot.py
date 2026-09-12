#!/usr/bin/env python3
"""
TLL OS Boot Script

One command to start TLL OS Reality Desktop.
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
from tllos.virtual_machine.agent import (
    TLLAgentSelf, TLLWorldModel, TLLExperienceMemory,
    TLLAgentConstitution, TLLAppRuntime, TLLAgentSpawner,
    TLLToolRuntime
)
from tllos.virtual_machine.desktop import TLLRealityDesktop


def main():
    print("=" * 60)
    print("TLL OS Reality Boot Sequence")
    print("=" * 60)
    print()

    # Step 1: Virtual Hardware
    print("[1/8] Virtual Hardware...")
    fb = TLLFramebuffer(1280, 800)
    wm = TLLWindowManager(fb)
    compositor = TLLCompositor(wm)
    print(f"  Display: {fb.width}x{fb.height}")

    # Step 2: Agent Core
    print("[2/8] Agent Core...")
    agent_self = TLLAgentSelf("tll-agent-0")
    agent_self.update_health(energy=98.0, risk_level="LOW")
    print(f"  Agent: {agent_self.get_self_state()['identity']} - ALIVE")

    # Step 3: World Model
    print("[3/8] World Model...")
    world = TLLWorldModel()
    world.add_object("Product DB", "service", object_id="db")
    world.add_object("Backend", "service", object_id="backend", dependencies=["db"])
    world.add_object("Frontend", "app", object_id="frontend", dependencies=["backend"])
    world.add_object("Mall", "app", object_id="mall", dependencies=["frontend"])
    print(f"  Objects: {world.get_world_summary()['total_objects']}")

    # Step 4: Experience
    print("[4/8] Experience & Constitution...")
    experience = TLLExperienceMemory()
    experience.record_experience("boot", "boot_ok", {}, {}, "SUCCESS", "System online", "LOW")
    constitution = TLLAgentConstitution()
    print(f"  Experiences: {experience.get_stats()['total_experiences']}")

    # Step 5: Tool Runtime
    print("[5/8] Tool Runtime...")
    tool_runtime = TLLToolRuntime(wm, compositor)
    print(f"  Tools: {len(tool_runtime.tool_handlers)} active")

    # Step 6: App Runtime
    print("[6/8] App Runtime...")
    app_runtime = TLLAppRuntime(wm, tool_runtime.process_mgr)
    print(f"  Apps: {app_runtime.get_stats()['total_apps']}")

    # Step 7: Reality Desktop
    print("[7/8] Reality Desktop...")
    desktop = TLLRealityDesktop(
        framebuffer=fb,
        agent_self=agent_self,
        world_model=world,
        experience=experience,
        app_runtime=app_runtime,
        tool_runtime=tool_runtime
    )

    # Render initial frame
    result = desktop.render()
    print(f"  Frame: {result['frame_hash'][:16]}...")

    # Step 8: Demo Command
    print("[8/8] Testing Command Loop...")
    cmd_result = desktop.submit_command("创建一个商城系统")
    print(f"  Command: {cmd_result['command']}")
    print(f"  Plan: {len(cmd_result['plan'])} steps")

    # Final render
    desktop.render()

    # Screenshot
    screenshot_path = PROJECT_ROOT / "tll_desktop_reality.png"
    ss = desktop.take_screenshot(str(screenshot_path))
    print(f"  Screenshot: {screenshot_path}")

    # Status
    print()
    print(desktop.get_status_text())
    print()

    print("=" * 60)
    print("TLL OS REALITY DESKTOP v1.0")
    print("Agent is alive. Awaiting owner commands.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
