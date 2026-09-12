#!/usr/bin/env python3
"""
TLL OS First Human Visible Boot Validator

5 Gates:
  Gate 1: Native Window Host
  Gate 2: LLM Adapter Registry
  Gate 3: Keyboard Input
  Gate 4: Evidence Viewer
  Gate 5: Full Boot
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_native_window():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.native import TLLENativeWindowHost
        fb = TLLFramebuffer(400, 300)
        host = TLLENativeWindowHost(fb, "Test")
        if host.fb.width == 400 and host.title == "Test":
            results.append(("Gate 1: Native Window Host", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Native Window Host", FAIL))
    return False


def gate2_llm_adapters():
    try:
        from tllos.virtual_machine.agent import TLLLLMAdapterRegistry
        registry = TLLLLMAdapterRegistry()
        adapters = registry.list_available()
        if "openai" in adapters and "doubao" in adapters and "local" in adapters:
            results.append(("Gate 2: LLM Adapter Registry", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: LLM Adapter Registry", FAIL))
    return False


def gate3_keyboard_input():
    try:
        from tllos.virtual_machine.agent import TLLInputManager
        im = TLLInputManager()
        im.submit("创建商城")
        cmd = im.get_next_command()
        if cmd.text == "创建商城":
            results.append(("Gate 3: Keyboard Input", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Keyboard Input", FAIL))
    return False


def gate4_evidence_viewer():
    try:
        from tllos.virtual_machine.agent import TLLEvidenceSystem
        evd = TLLEvidenceSystem()
        rec = evd.record("create_file", "test", "LOW", True, "success")
        if rec.evidence_hash and len(rec.evidence_hash) == 16:
            results.append(("Gate 4: Evidence Viewer", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Evidence Viewer", FAIL))
    return False


def gate5_full_boot():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLExecutionDesktop
        from tllos.virtual_machine.agent import (
            TLLAgentSelf, TLLWorldModel, TLLExperienceMemory,
            TLLApprovalGate, TLLEvidenceSystem, TLLInputManager
        )

        fb = TLLFramebuffer(800, 600)
        desktop = TLLExecutionDesktop(
            framebuffer=fb,
            agent_self=TLLAgentSelf("test"),
            world_model=TLLWorldModel(),
            experience=TLLExperienceMemory(),
            approval_gate=TLLApprovalGate(),
            evidence_system=TLLEvidenceSystem(),
            input_manager=TLLInputManager()
        )
        result = desktop.render()
        if result["panels_rendered"] >= 3:
            results.append(("Gate 5: Full Boot", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 5: Full Boot", FAIL))
    return False


def main():
    print("=" * 60)
    print("TLL OS First Human Visible Boot Validator")
    print("=" * 60)
    print()

    gate1_native_window()
    gate2_llm_adapters()
    gate3_keyboard_input()
    gate4_evidence_viewer()
    gate5_full_boot()

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
