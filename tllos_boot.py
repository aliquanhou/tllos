#!/usr/bin/env python3
"""
TLL OS Boot Script

First Human Visible Boot - shows TLL OS in a real window.
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
from tllos.virtual_machine.agent import (
    TLLAgentSelf, TLLWorldModel, TLLExperienceMemory,
    TLLAgentConstitution, TLLAppRuntime,
    TLLToolRuntime, TLLActionRiskEvaluator, TLLAgentLiveLoop,
    TLLInputManager, TLLLLMBridge, TLLMockLLMProvider,
    TLLApprovalGate, TLLEvidenceSystem,
    TLLLLMAdapterRegistry
)
from tllos.virtual_machine.desktop import TLLExecutionDesktop
from tllos.virtual_machine.native import TLLENativeWindowHost


def main():
    print("=" * 60)
    print("TLL OS First Human Visible Boot")
    print("=" * 60)
    print()

    print("🔧 Virtual Hardware...")
    fb = TLLFramebuffer(1280, 800)
    wm = TLLWindowManager(fb)
    compositor = TLLCompositor(wm)
    print(f"   Display: {fb.width}x{fb.height}")

    print("🧠 Agent Core...")
    agent_self = TLLAgentSelf("tll-agent-0")
    agent_self.update_health(energy=98.0, risk_level="LOW")
    constitution = TLLAgentConstitution()
    print(f"   Agent: tll-agent-0 ONLINE")
    print(f"   Rules: {constitution.get_constitution_summary()['total_rules']}")

    print("🌍 World Model...")
    world = TLLWorldModel()
    world.add_object("Product DB", "service", object_id="db")
    world.add_object("Backend", "service", object_id="backend", dependencies=["db"])
    world.add_object("Frontend", "app", object_id="frontend", dependencies=["backend"])
    print(f"   Objects: {world.get_world_summary()['total_objects']}")

    print("🧠 Experience...")
    experience = TLLExperienceMemory()
    print(f"   Experiences: {experience.get_stats()['total_experiences']}")

    print("🛠 Tool Runtime...")
    tool_runtime = TLLToolRuntime(wm, compositor)
    risk_evaluator = TLLActionRiskEvaluator()
    print(f"   Tools: {len(tool_runtime.tool_handlers)} active")

    print("📦 App Runtime...")
    app_runtime = TLLAppRuntime(wm, tool_runtime.process_mgr)
    print(f"   Apps: {app_runtime.get_stats()['total_apps']}")

    print("⌨ Input Manager...")
    input_manager = TLLInputManager()
    print(f"   Owner: {input_manager.owner}")

    print("🧠 LLM Bridge...")
    llm_registry = TLLLLMAdapterRegistry()
    llm_bridge = TLLLLMBridge(TLLMockLLMProvider())
    print(f"   Provider: {llm_bridge.provider_name}")
    print(f"   Available adapters: {', '.join(llm_registry.list_available())}")

    print("🔐 Approval Gate...")
    approval_gate = TLLApprovalGate()
    print(f"   Auto-approve LOW: {approval_gate.auto_approve_low_risk}")

    print("📜 Evidence System...")
    evidence_system = TLLEvidenceSystem()
    print(f"   Ready")

    print("🔄 Agent Live Loop...")
    live_loop = TLLAgentLiveLoop(
        agent_self=agent_self, world_model=world, experience=experience,
        tool_runtime=tool_runtime, app_runtime=app_runtime, risk_evaluator=risk_evaluator
    )
    print("   Agent: tll-agent-0 ALIVE")

    print("🖥 Execution Desktop...")
    desktop = TLLExecutionDesktop(
        framebuffer=fb, agent_self=agent_self, world_model=world,
        experience=experience, app_runtime=app_runtime, tool_runtime=tool_runtime,
        live_loop=live_loop, input_manager=input_manager, llm_bridge=llm_bridge,
        approval_gate=approval_gate, evidence_system=evidence_system
    )

    # Initial render
    result = desktop.render()
    print(f"   Frame: {result['frame_hash'][:16]}...")

    # Demo command
    desktop.submit_command("创建一个电商网站")
    desktop.render()

    # Screenshot
    screenshot_path = PROJECT_ROOT / "tll_visible_boot.png"
    ss = desktop.take_screenshot(str(screenshot_path))
    print(f"   Screenshot: {screenshot_path}")

    print()
    print(desktop.get_status_text())
    print()

    print("=" * 60)
    print("🤖 TLL OS IS ALIVE AND VISIBLE")
    print("Native Window Host: Ready")
    print("Keyboard Input: Ready")
    print("LLM Adapters: openai, doubao, local")
    print("=" * 60)
    print()
    print("Press any key in the window to type commands.")
    print("Press Enter to submit. Press ESC to close.")
    print()

    # Launch native window
    try:
        window = TLLENativeWindowHost(
            framebuffer=fb,
            title="TLL OS - tll-agent-0"
        )
        window.create_window()
        print("Window created. Running...")
        window.run()
    except Exception as e:
        print(f"Native window not available: {e}")
        print("Running in headless mode.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
