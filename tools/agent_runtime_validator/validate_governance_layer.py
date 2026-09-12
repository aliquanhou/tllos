#!/usr/bin/env python3
"""
TLL OS Agent Experience & Governance Layer Validator

5 Gates:
  Gate 1: Experience Memory
  Gate 2: Constitution Learning
  Gate 3: Family Protocol
  Gate 4: Learning Loop
  Gate 5: Integration
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_experience_memory():
    try:
        from tllos.virtual_machine.agent import TLLExperienceMemory
        mem = TLLExperienceMemory()
        exp = mem.record_experience(
            action="test", evidence="test",
            world_before={}, world_after={},
            result="FAILED", lesson="test lesson",
            risk_level="HIGH"
        )
        stats = mem.get_stats()
        if stats["total_experiences"] == 1 and stats["lessons_learned"] == 1:
            results.append(("Gate 1: Experience Memory", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Experience Memory", FAIL))
    return False


def gate2_constitution_learning():
    try:
        from tllos.virtual_machine.agent import TLLConstitutionLearning, TLLExperienceMemory
        mem = TLLExperienceMemory()
        learning = TLLConstitutionLearning()

        exp = mem.record_experience(
            action="bad_action", evidence="test",
            world_before={}, world_after={},
            result="FAILED", lesson="don't do this",
            risk_level="HIGH"
        )

        proposal = learning.learn_from_experience(exp)
        review = learning.review_proposal(proposal.proposal_id, approved=True)

        if review["status"] == "APPROVED":
            results.append(("Gate 2: Constitution Learning", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Constitution Learning", FAIL))
    return False


def gate3_family_protocol():
    try:
        from tllos.virtual_machine.agent import TLLAgentFamilyProtocol
        family = TLLAgentFamilyProtocol()

        child = family.spawn_with_inheritance(
            parent_id="parent", child_id="child", child_name="Child",
            parent_capabilities=["tool1", "tool2"],
            parent_memory_summary="test",
            parent_constitutional_rules=["rule1"],
            parent_safety_boundaries=["boundary1"]
        )

        if child["inherited_tools"] == 2 and child["inherited_rules"] == 1:
            results.append(("Gate 3: Family Protocol", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Family Protocol", FAIL))
    return False


def gate4_learning_loop():
    """Test the full learning loop: experience -> proposal -> approval."""
    try:
        from tllos.virtual_machine.agent import TLLExperienceMemory, TLLConstitutionLearning
        mem = TLLExperienceMemory()
        learning = TLLConstitutionLearning()

        # Multiple failures generate multiple proposals
        for i in range(3):
            exp = mem.record_experience(
                action=f"action_{i}", evidence=f"ev_{i}",
                world_before={}, world_after={},
                result="FAILED", lesson=f"lesson {i}",
                risk_level="HIGH"
            )
            learning.learn_from_experience(exp)

        pending = learning.get_pending_proposals()
        if len(pending) == 3:
            results.append(("Gate 4: Learning Loop", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: Learning Loop", FAIL))
    return False


def gate5_integration():
    try:
        from tllos.virtual_machine.agent import (
            TLLExperienceMemory, TLLConstitutionLearning,
            TLLAgentFamilyProtocol, TLLWorldModel
        )

        # Build world
        world = TLLWorldModel()
        world.add_object("DB", "service", object_id="db")

        # Experience
        mem = TLLExperienceMemory()
        exp = mem.record_experience(
            action="delete_db", evidence="hash123",
            world_before={"db": "active"}, world_after={"db": "deleted"},
            result="FAILED", lesson="Deleting DB breaks world",
            risk_level="CRITICAL"
        )

        # Learn from experience
        learning = TLLConstitutionLearning()
        proposal = learning.learn_from_experience(exp)
        learning.review_proposal(proposal.proposal_id, approved=True)

        # Family protocol - child inherits learned rules
        family = TLLAgentFamilyProtocol()
        child = family.spawn_with_inheritance(
            parent_id="parent", child_id="child", child_name="Learner",
            parent_capabilities=["storage.read"],
            parent_memory_summary="Has DB deletion experience",
            parent_constitutional_rules=["No Evidence No Destruction", "DB deletion requires approval"],
            parent_safety_boundaries=["No DB deletion"]
        )

        stats = mem.get_stats()
        if stats["failures"] == 1 and len(learning.get_approved_rules()) == 1:
            results.append(("Gate 5: Integration", PASS))
            return True
    except Exception as e:
        results.append(("Gate 5: Integration", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Agent Experience & Governance Layer Validator")
    print("=" * 60)
    print()

    gate1_experience_memory()
    gate2_constitution_learning()
    gate3_family_protocol()
    gate4_learning_loop()
    gate5_integration()

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
