#!/usr/bin/env python3
"""
TLL OS Execution Layer Validator

5 Gates:
  Gate 1: Input System
  Gate 2: LLM Bridge
  Gate 3: Approval Gate
  Gate 4: Evidence System
  Gate 5: Full Pipeline
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_input_system():
    try:
        from tllos.virtual_machine.agent import TLLInputManager
        im = TLLInputManager()
        cmd = im.submit("create mall")
        if cmd.id == "cmd_0001" and cmd.text == "create mall" and im.has_pending():
            results.append(("Gate 1: Input System", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Input System", FAIL))
    return False


def gate2_llm_bridge():
    try:
        from tllos.virtual_machine.agent import TLLLLMBridge, TLLMockLLMProvider
        bridge = TLLLLMBridge(TLLMockLLMProvider())
        thought = bridge.think("create mall", {})
        plan = bridge.plan("create mall", {})
        if thought["confidence"] == 0.85 and len(plan) >= 3:
            results.append(("Gate 2: LLM Bridge", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: LLM Bridge", FAIL))
    return False


def gate3_approval_gate():
    try:
        from tllos.virtual_machine.agent import TLLApprovalGate
        gate = TLLApprovalGate()
        req = gate.request_approval("storage.delete", "delete old db", "HIGH",
                                     impact=["backend", "frontend"])
        if req.status == "PENDING" and gate.has_pending():
            gate.approve(req.id)
            if gate.get_pending() == []:
                results.append(("Gate 3: Approval Gate", PASS))
                return True
    except Exception as e:
        pass
    results.append(("Gate 3: Approval Gate", FAIL))
    return False


def gate4_evidence_system():
    try:
        from tllos.virtual_machine.agent import TLLEvidenceSystem
        evd = TLLEvidenceSystem()
        rec = evd.record("create_file", "create mall backend", "LOW", True, "success")
        if rec.evidence_hash and evd.get_stats()["total_records"] == 1:
            results.append(("Gate 4: Evidence System", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Evidence System", FAIL))
    return False


def gate5_full_pipeline():
    try:
        from tllos.virtual_machine import TLLFramebuffer
        from tllos.virtual_machine.desktop import TLLExecutionDesktop
        from tllos.virtual_machine.agent import (
            TLLAgentSelf, TLLWorldModel, TLLExperienceMemory,
            TLLApprovalGate, TLLEvidenceSystem, TLLInputManager, TLLLLMBridge
        )

        fb = TLLFramebuffer(800, 600)
        desktop = TLLExecutionDesktop(
            framebuffer=fb,
            agent_self=TLLAgentSelf("test"),
            world_model=TLLWorldModel(),
            experience=TLLExperienceMemory(),
            approval_gate=TLLApprovalGate(),
            evidence_system=TLLEvidenceSystem(),
            input_manager=TLLInputManager(),
            llm_bridge=TLLLLMBridge()
        )

        result = desktop.submit_command("build a website")
        status = desktop.get_status_text()

        if "EXECUTION STATUS" in status and "Evidence:" in status:
            results.append(("Gate 5: Full Pipeline", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 5: Full Pipeline", FAIL))
    return False


def main():
    print("=" * 60)
    print("TLL OS Execution Layer Validator")
    print("=" * 60)
    print()

    gate1_input_system()
    gate2_llm_bridge()
    gate3_approval_gate()
    gate4_evidence_system()
    gate5_full_pipeline()

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
