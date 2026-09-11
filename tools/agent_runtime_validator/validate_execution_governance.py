#!/usr/bin/env python3
"""
TLL OS Execution Governance Validator
验证 Execution Governance 层的协议完整性。

Gates:
- Gate 1: Governance Schema Exists
- Gate 2: Policy Exists
- Gate 3: Decision Schema Valid
- Gate 4: Invalid Execution Rejected
- Gate 5: Approved Execution Contains Evidence

用法：
    python tools/agent_runtime_validator/validate_execution_governance.py

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
    print("TLL OS Execution Governance Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Governance Schema Exists
    print("--- Gate 1: Governance Schema Exists ---")
    gov_files = [
        "tllos/agent_runtime/execution_governance/README.md",
        "tllos/agent_runtime/execution_governance/architecture.md",
        "tllos/agent_runtime/execution_governance/governance_model.md",
        "tllos/agent_runtime/execution_governance/governance_state.json",
        "tllos/agent_runtime/execution_governance/execution_governance_policy.json",
        "tllos/agent_runtime/execution_governance/governance_decision.json",
    ]
    all_exist = True
    for file_path in gov_files:
        if not check_file_exists(file_path):
            print(f"  ❌ FAIL: {file_path} not found")
            all_exist = False
            all_passed = False
    if all_exist:
        print(f"  ✅ PASS: all governance files exist (6 files)")
        results.append(("Gate 1: Governance Schema Exists", "PASS"))

    # Gate 2: Policy Exists
    print()
    print("--- Gate 2: Policy Exists ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_governance/execution_governance_policy.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 2: Policy Exists", "FAIL"))
    else:
        if "governance_rules" in data:
            print(f"  ✅ PASS: governance_rules defined")
            results.append(("Gate 2: Policy Exists", "PASS"))
        else:
            print(f"  ❌ FAIL: governance_rules missing")
            all_passed = False
            results.append(("Gate 2: Policy Exists", "FAIL"))

    # Gate 3: Decision Schema Valid
    print()
    print("--- Gate 3: Decision Schema Valid ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_governance/governance_decision.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 3: Decision Schema Valid", "FAIL"))
    else:
        required = ["execution_id", "agent_id", "decision", "reason", "risk_level", "policy_checks", "evidence_binding", "timestamp"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 3: Decision Schema Valid", "FAIL"))
        else:
            print(f"  ✅ PASS: all required fields present")
            results.append(("Gate 3: Decision Schema Valid", "PASS"))

    # Gate 4: Invalid Execution Rejected
    print()
    print("--- Gate 4: Invalid Execution Rejected ---")
    ok, policy = validate_json_file("tllos/agent_runtime/execution_governance/execution_governance_policy.json")
    if not ok:
        print(f"  ❌ FAIL: {policy}")
        all_passed = False
        results.append(("Gate 4: Invalid Execution Rejected", "FAIL"))
    else:
        default_policy = policy.get("default_policy", {})
        all_reject = (
            default_policy.get("unrecognized_risk") == "REJECT"
            and default_policy.get("missing_identity") == "REJECT"
            and default_policy.get("missing_capability") == "REJECT"
            and default_policy.get("missing_permission") == "REJECT"
            and default_policy.get("missing_evidence") == "REJECT"
        )
        if all_reject:
            print(f"  ✅ PASS: all invalid executions default REJECT")
            results.append(("Gate 4: Invalid Execution Rejected", "PASS"))
        else:
            print(f"  ❌ FAIL: default policy not all REJECT")
            all_passed = False
            results.append(("Gate 4: Invalid Execution Rejected", "FAIL"))

    # Gate 5: Approved Execution Contains Evidence
    print()
    print("--- Gate 5: Approved Execution Contains Evidence ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_governance/governance_decision.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 5: Approved Execution Contains Evidence", "FAIL"))
    else:
        required = data.get("required_fields", [])
        if "evidence_binding" in required:
            print(f"  ✅ PASS: evidence_binding is required for all decisions")
            results.append(("Gate 5: Approved Execution Contains Evidence", "PASS"))
        else:
            print(f"  ❌ FAIL: evidence_binding not required")
            all_passed = False
            results.append(("Gate 5: Approved Execution Contains Evidence", "FAIL"))

    print()
    print("=" * 60)
    if all_passed:
        print("Execution Governance Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Execution Governance Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
