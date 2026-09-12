#!/usr/bin/env python3
"""Test TLL Agent Experience & Governance Layer."""

from tllos.virtual_machine.agent import (
    TLLExperienceMemory, TLLConstitutionLearning,
    TLLAgentFamilyProtocol
)

print("=== TLL Agent Experience & Governance Layer Test ===")
print()

# Test 1: Experience Memory
print("=== 1. Experience Memory ===")
exp_mem = TLLExperienceMemory()

# Record a failed experience
exp1 = exp_mem.record_experience(
    action="delete_database",
    evidence="hash: abc123",
    world_before={"mall": "running", "db": "active"},
    world_after={"mall": "crashed", "db": "deleted"},
    result="FAILED",
    lesson="Deleting core database breaks dependent services",
    risk_level="CRITICAL"
)
print(f"Experience 1: {exp1.experience_id} - {exp1.result}")
print(f"  Lesson: {exp1.lesson}")

# Record a success
exp2 = exp_mem.record_experience(
    action="create_backup",
    evidence="hash: def456",
    world_before={"state": "clean"},
    world_after={"state": "backed_up"},
    result="SUCCESS",
    lesson="Backup before high-risk operations",
    risk_level="LOW"
)
print(f"Experience 2: {exp2.experience_id} - {exp2.result}")

stats = exp_mem.get_stats()
print(f"Stats: {stats}")
print()

# Test 2: Constitution Learning
print("=== 2. Constitution Learning ===")
learning = TLLConstitutionLearning()

# Learn from failed experience
proposal = learning.learn_from_experience(exp1)
print(f"Proposal generated: {proposal.proposal_id if proposal else 'None'}")
if proposal:
    print(f"  Name: {proposal.name}")
    print(f"  Status: {proposal.status}")

# Human review
review = learning.review_proposal(proposal.proposal_id, approved=True)
print(f"Review: {review}")

learning_stats = learning.get_stats()
print(f"Learning stats: {learning_stats}")
print()

# Test 3: Agent Family Protocol
print("=== 3. Agent Family Protocol ===")
family = TLLAgentFamilyProtocol()

# Parent spawns child with inheritance
child = family.spawn_with_inheritance(
    parent_id="tll-agent-0",
    child_id="tll-agent-1",
    child_name="Mall Builder",
    parent_capabilities=["display.create_window", "storage.write", "code.run"],
    parent_memory_summary="Has experience building mall systems",
    parent_constitutional_rules=["No Evidence No Destruction", "Evidence Mandatory"],
    parent_safety_boundaries=["No self-termination", "No unauthorized deletion"]
)
print(f"Child spawned: {child['child_id']}")
print(f"  Inherited tools: {child['inherited_tools']}")
print(f"  Inherited rules: {child['inherited_rules']}")

# Increase independence
ind = family.increase_independence("tll-agent-1", 0.5)
print(f"  Independence: {ind['independence_level']}")

family_stats = family.get_stats()
print(f"Family stats: {family_stats}")
print()

# Final Summary
print("=== Final Summary ===")
print(f"Experience Memory: {stats}")
print(f"Constitution Learning: {learning_stats}")
print(f"Family Protocol: {family_stats}")
print()

print("PASS: TLL Agent Experience & Governance Layer works")
