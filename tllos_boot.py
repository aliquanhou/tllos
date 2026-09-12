#!/usr/bin/env python3
"""
TLL OS Boot Script

TLL OS Reality Control Center Boot.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
from tllos.virtual_machine.agent import (
    TLLAgentSelf, TLLWorldModel, TLLExperienceMemory,
    TLLAgentConstitution, TLLAppRuntime, TLLAgentSpawner,
    TLLToolRuntime, TLLActionRiskEvaluator, TLLAgentLiveLoop
)
from tllos.virtual_machine.desktop import TLLControlCenterDesktop


def main():
    print("=" * 60)
    print("TLL OS Reality Control Center Boot")
    print("=" * 60)
    print()

    print("🔧 Loading Virtual Hardware...")
    fb = TLLFramebuffer(1280, 800)
    wm = TLLWindowManager(fb)
    compositor = TLLCompositor(wm)
    print(f"   Display: {fb.width}x{fb.height}")

    print("🧠 Loading Agent Constitution...")
    agent_self = TLLAgentSelf("tll-agent-0")
    agent_self.update_health(energy=98.0, risk_level="LOW")
    constitution = TLLAgentConstitution()
    print(f"   Rules: {constitution.get_constitution_summary()['total_rules']}")

    print("🌍 Loading World Model...")
    world = TLLWorldModel()
    world.add_object("Product DB", "service", object_id="db")
    world.add_object("Backend", "service", object_id="backend", dependencies=["db"])
    world.add_object("Frontend", "app", object_id="frontend", dependencies=["backend"])
    print(f"   Objects: {world.get_world_summary()['total_objects']}")

    print("🧠 Loading Experience...")
    experience = TLLExperienceMemory()
    experience.record_experience("boot", "boot_ok", {}, {}, "SUCCESS", "System online", "LOW")
    print(f"   Experiences: {experience.get_stats()['total_experiences']}")

    print("🛠 Loading Tool Runtime...")
    tool_runtime = TLLToolRuntime(wm, compositor)
    risk_evaluator = TLLActionRiskEvaluator()
    print(f"   Tools: {len(tool_runtime.tool_handlers)} active")

    print("📦 Loading App Runtime...")
    app_runtime = TLLAppRuntime(wm, tool_runtime.process_mgr)
    print(f"   Apps: {app_runtime.get_stats()['total_apps']}")

    print("🔄 Starting Agent Live Loop...")
    live_loop = TLLAgentLiveLoop(
        agent_self=agent_self,
        world_model=world,
        experience=experience,
        tool_runtime=tool_runtime,
        app_runtime=app_runtime,
        risk_evaluator=risk_evaluator
    )
    print("   Agent: tll-agent-0 ALIVE")

    print("🖥 Starting Control Center...")
    desktop = TLLControlCenterDesktop(
        framebuffer=fb,
        agent_self=agent_self,
        world_model=world,
        experience=experience,
        app_runtime=app_runtime,
        tool_runtime=tool_runtime,
        live_loop=live_loop
    )

    # Initial render
    result = desktop.render()
    print(f"   Frame: {result['frame_hash'][:16]}...")

    print("🤖 Testing Agent Command...")
    cmd = desktop.submit_command("创建一个商城系统")
    print(f"   Goal: {cmd.get('goal', 'N/A')}")
    print(f"   Plan: {len(cmd.get('plan', []))} steps")

    # Final render
    desktop.render()

    # Screenshot
    screenshot_path = PROJECT_ROOT / "tll_control_center.png"
    ss = desktop.take_screenshot(str(screenshot_path))
    print(f"   Screenshot: {screenshot_path}")

    # Status
    print()
    print(desktop.get_status_text())
    print()

    print("=" * 60)
    print("🤖 TLL OS AGENT IS ALIVE")
    print("Control Center Ready.")
    print("Owner can now issue commands.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
