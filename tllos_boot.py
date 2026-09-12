#!/usr/bin/env python3
"""
TLL OS Boot Script

One command to start TLL OS Desktop.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
from tllos.virtual_machine.agent import (
    TLLAgentSelf, TLLWorldModel, TLLExperienceMemory,
    TLLAgentConstitution, TLLAppRuntime, TLLAgentSpawner
)
from tllos.virtual_machine.desktop import TLLDesktopSurface


def main():
    print("=" * 60)
    print("TLL OS Boot Sequence")
    print("=" * 60)
    print()

    # Step 1: Virtual Hardware
    print("[1/6] Initializing Virtual Hardware...")
    fb = TLLFramebuffer(1280, 800)
    wm = TLLWindowManager(fb)
    compositor = TLLCompositor(wm)
    print(f"  Display: {fb.width}x{fb.height}")
    print()

    # Step 2: Agent Core
    print("[2/6] Initializing Agent Core...")
    agent_self = TLLAgentSelf("tll-agent-0")
    agent_self.update_health(energy=95.0, risk_level="LOW")
    print(f"  Agent: {agent_self.get_self_state()['identity']}")
    print(f"  State: {agent_self.get_health_summary()['survival']}")
    print()

    # Step 3: World Model
    print("[3/6] Initializing World Model...")
    world = TLLWorldModel()
    world.add_object("Product Database", "service", object_id="svc-db")
    world.add_object("Backend API", "service", object_id="svc-backend", dependencies=["svc-db"])
    world.add_object("Frontend UI", "app", object_id="app-frontend", dependencies=["svc-backend"])
    world.add_object("Mall App", "app", object_id="app-mall", dependencies=["app-frontend"])
    print(f"  Objects: {world.get_world_summary()['total_objects']}")
    print()

    # Step 4: Experience & Constitution
    print("[4/6] Initializing Experience & Constitution...")
    experience = TLLExperienceMemory()
    experience.record_experience(
        action="system_boot", evidence="boot_complete",
        world_before={}, world_after={"agent": "online"},
        result="SUCCESS", lesson="System boot successful",
        risk_level="LOW"
    )
    constitution = TLLAgentConstitution()
    print(f"  Experiences: {experience.get_stats()['total_experiences']}")
    print(f"  Rules: {constitution.get_constitution_summary()['total_rules']}")
    print()

    # Step 5: App Runtime
    print("[5/6] Initializing App Runtime...")
    app_runtime = TLLAppRuntime(wm, None)
    spawner = TLLAgentSpawner()
    print(f"  Apps: {app_runtime.get_stats()['total_apps']}")
    print()

    # Step 6: Desktop
    print("[6/6] Initializing Desktop Surface...")
    desktop = TLLDesktopSurface(
        framebuffer=fb,
        agent_self=agent_self,
        world_model=world,
        experience=experience,
        constitution=constitution,
        app_runtime=app_runtime,
        spawner=spawner
    )
    result = desktop.render()
    print(f"  Frame: {result['frame_hash'][:16]}...")
    print(f"  Resolution: {result['width']}x{result['height']}")
    print()

    # Screenshot
    screenshot_path = PROJECT_ROOT / "tll_desktop_snapshot.png"
    desktop.take_screenshot(str(screenshot_path))
    print(f"Desktop Screenshot: {screenshot_path}")
    print()

    # Status text
    status_text = desktop.get_status_text()
    print(status_text)
    print()

    print("=" * 60)
    print("TLL OS is ONLINE")
    print("Awaiting user commands...")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
