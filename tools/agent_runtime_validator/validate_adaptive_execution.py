#!/usr/bin/env python3
"""
TLL OS Adaptive Execution Validator
验证 Adaptive Execution 层的协议完整性。

Gates:
- Gate 1: Feedback Schema
- Gate 2: Evidence Binding
- Gate 3: Proposal Integrity
- Gate 4: Governance Required
- Gate 5: No Direct Execution

用法：
    python tools/agent_runtime_validator/validate_adaptive_execution.py

退出码：
    0: 全部验证通过
    1: 存在验证失败
"""

import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))


def validate_json_file(file_path):
    full_path = os.path.join(PROJECT_ROOT, file_path)
    if not os.path.exists(full_path):
        return False, f"File not found: {file_path}"
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"
    except Exception as e:
        return False, f"Read error: {e}"
    return True, data


def check_file_exists(file_path):
    full_path = os.path.join(PROJECT_ROOT, file_path)
    return os.path.exists(full_path)


def main():
    print("=" * 60)
    print("TLL OS Adaptive Execution Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Feedback Schema
    print("--- Gate 1: Feedback Schema ---")
    ok, data = validate_json_file("tllos/agent_runtime/adaptive_execution/adaptive_feedback.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 1: Feedback Schema", "FAIL"))
    else:
        required = ["execution_id", "observation_ref", "metrics_ref", "insight_ref", "feedback_type", "feedback_value", "evidence_ref", "audit_ref"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 1: Feedback Schema", "FAIL"))
        else:
            print(f"  ✅ PASS: all required fields present")
            results.append(("Gate 1: Feedback Schema", "PASS"))

    # Gate 2: Evidence Binding
    print()
    print("--- Gate 2: Evidence Binding ---")
    ok, data = validate_json_file("tllos/agent_runtime/adaptive_execution/adaptive_feedback.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 2: Evidence Binding", "FAIL"))
    else:
        required = data.get("required_fields", [])
        if "evidence_ref" in required and "audit_ref" in required:
            print(f"  ✅ PASS: evidence_ref and audit_ref are required")
            results.append(("Gate 2: Evidence Binding", "PASS"))
        else:
            print(f"  ❌ FAIL: evidence_ref/audit_ref not required")
            all_passed = False
            results.append(("Gate 2: Evidence Binding", "FAIL"))

    # Gate 3: Proposal Integrity
    print()
    print("--- Gate 3: Proposal Integrity ---")
    ok, data = validate_json_file("tllos/agent_runtime/adaptive_execution/adaptation_proposal.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 3: Proposal Integrity", "FAIL"))
    else:
        allowed = data.get("allowed_proposal_types", [])
        prohibited = data.get("prohibited_proposal_types", [])
        has_allowed = len(allowed) > 0
        has_prohibited = len(prohibited) > 0
        if has_allowed and has_prohibited:
            print(f"  ✅ PASS: allowed and prohibited types defined")
            results.append(("Gate 3: Proposal Integrity", "PASS"))
        else:
            print(f"  ❌ FAIL: proposal type integrity incomplete")
            all_passed = False
            results.append(("Gate 3: Proposal Integrity", "FAIL"))

    # Gate 4: Governance Required
    print()
    print("--- Gate 4: Governance Required ---")
    boundary_file = "tllos/agent_runtime/adaptive_execution/adaptive_decision_boundary.md"
    if check_file_exists(boundary_file):
        with open(os.path.join(PROJECT_ROOT, boundary_file), "r", encoding="utf-8") as f:
            content = f.read()
        has_governance = "Governance Review" in content or "Governance" in content
        has_required = "必须经过" in content or "必须" in content
        if has_governance and has_required:
            print(f"  ✅ PASS: governance review required")
            results.append(("Gate 4: Governance Required", "PASS"))
        else:
            print(f"  ❌ FAIL: governance review not required")
            all_passed = False
            results.append(("Gate 4: Governance Required", "FAIL"))
    else:
        print(f"  ❌ FAIL: adaptive_decision_boundary.md not found")
        all_passed = False
        results.append(("Gate 4: Governance Required", "FAIL"))

    # Gate 5: No Direct Execution
    print()
    print("--- Gate 5: No Direct Execution ---")
    arch_file = "tllos/agent_runtime/adaptive_execution/architecture.md"
    if check_file_exists(arch_file):
        with open(os.path.join(PROJECT_ROOT, arch_file), "r", encoding="utf-8") as f:
            content = f.read()
        has_no_execute = "不直接执行" in content or "不能直接执行" in content or "Recommend" in content
        has_no_modify = "不执行任何实际操作" in content or "不修改任何执行状态" in content
        if has_no_execute and has_no_modify:
            print(f"  ✅ PASS: adaptive layer is recommend-only, no direct execution")
            results.append(("Gate 5: No Direct Execution", "PASS"))
        else:
            print(f"  ❌ FAIL: no direct execution rule not found")
            all_passed = False
            results.append(("Gate 5: No Direct Execution", "FAIL"))
    else:
        print(f"  ❌ FAIL: architecture.md not found")
        all_passed = False
        results.append(("Gate 5: No Direct Execution", "FAIL"))

    # Also check directory structure
    print()
    print("--- Directory Structure ---")
    adaptive_files = [
        "tllos/agent_runtime/adaptive_execution/README.md",
        "tllos/agent_runtime/adaptive_execution/architecture.md",
        "tllos/agent_runtime/adaptive_execution/adaptive_model.md",
        "tllos/agent_runtime/adaptive_execution/feedback_loop.md",
        "tllos/agent_runtime/adaptive_execution/adaptation_policy.md",
        "tllos/agent_runtime/adaptive_execution/adaptive_feedback.json",
        "tllos/agent_runtime/adaptive_execution/adaptation_proposal.json",
        "tllos/agent_runtime/adaptive_execution/adaptive_decision_boundary.md",
    ]
    for file_path in adaptive_files:
        if check_file_exists(file_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Adaptive Execution Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Adaptive Execution Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
