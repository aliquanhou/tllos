#!/usr/bin/env python3
"""
TLL OS Execution Boundary Validator
验证 Execution Boundary 层的协议完整性。

Gates:
- Gate 1: Runtime Target Schema
- Gate 2: Execution Policy
- Gate 3: Lifecycle State Machine
- Gate 4: Result Verification
- Gate 5: Audit Binding

用法：
    python tools/agent_runtime_validator/validate_execution_boundary.py

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


def read_file_content(file_path):
    full_path = os.path.join(PROJECT_ROOT, file_path)
    if not os.path.exists(full_path):
        return None
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    print("=" * 60)
    print("TLL OS Execution Boundary Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Runtime Target Schema
    print("--- Gate 1: Runtime Target Schema ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_boundary/schemas/runtime_target.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 1: Runtime Target Schema", "FAIL"))
    else:
        required = ["target_id", "runtime_type", "version", "capabilities", "status", "security_level"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 1: Runtime Target Schema", "FAIL"))
        else:
            print(f"  ✅ PASS: all required fields present")
            results.append(("Gate 1: Runtime Target Schema", "PASS"))

    # Gate 2: Execution Policy
    print()
    print("--- Gate 2: Execution Policy ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_boundary/schemas/execution_policy.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 2: Execution Policy", "FAIL"))
    else:
        required = ["identity_verified", "capability_declared", "permission_approved", "evidence_present", "runtime_target_registered", "policy_approved"]
        missing = [f for f in required if f not in data.get("required_checks", [])]
        if missing:
            print(f"  ❌ FAIL: missing required checks: {missing}")
            all_passed = False
            results.append(("Gate 2: Execution Policy", "FAIL"))
        else:
            print(f"  ✅ PASS: all policy checks present")
            results.append(("Gate 2: Execution Policy", "PASS"))

    # Gate 3: Lifecycle State Machine
    print()
    print("--- Gate 3: Lifecycle State Machine ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_boundary/lifecycle/execution_states.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 3: Lifecycle State Machine", "FAIL"))
    else:
        states = data.get("states", [])
        required_states = ["CREATED", "VALIDATING", "AUTHORIZED", "READY", "EXECUTING", "COMPLETED"]
        missing = [s for s in required_states if s not in states]
        if missing:
            print(f"  ❌ FAIL: missing states: {missing}")
            all_passed = False
            results.append(("Gate 3: Lifecycle State Machine", "FAIL"))
        else:
            print(f"  ✅ PASS: all required states present")
            results.append(("Gate 3: Lifecycle State Machine", "PASS"))

    # Gate 4: Result Verification
    print()
    print("--- Gate 4: Result Verification ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_boundary/schemas/execution_result_validation.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 4: Result Verification", "FAIL"))
    else:
        required = ["execution_id", "agent_id", "runtime_target", "permission", "evidence", "audit_event", "result_hash", "status"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 4: Result Verification", "FAIL"))
        else:
            print(f"  ✅ PASS: all result fields present")
            results.append(("Gate 4: Result Verification", "PASS"))

    # Gate 5: Audit Binding
    print()
    print("--- Gate 5: Audit Binding ---")
    audit_file = "tllos/agent_runtime/audit_ledger/audit_event.json"
    ok, audit_data = validate_json_file(audit_file)
    if not ok:
        print(f"  ❌ FAIL: {audit_data}")
        all_passed = False
        results.append(("Gate 5: Audit Binding", "FAIL"))
    else:
        required_events = ["EXECUTION_CREATED", "EXECUTION_VALIDATING", "EXECUTION_AUTHORIZED", "EXECUTION_STARTED", "EXECUTION_COMPLETED"]
        existing_events = audit_data.get("event_types", [])
        missing = [e for e in required_events if e not in existing_events]
        if missing:
            print(f"  ❌ FAIL: missing audit events: {missing}")
            all_passed = False
            results.append(("Gate 5: Audit Binding", "FAIL"))
        else:
            print(f"  ✅ PASS: all required audit events present")
            results.append(("Gate 5: Audit Binding", "PASS"))

    # Also check directory structure
    print()
    print("--- Directory Structure ---")
    boundary_files = [
        "tllos/agent_runtime/execution_boundary/README.md",
        "tllos/agent_runtime/execution_boundary/architecture.md",
        "tllos/agent_runtime/execution_boundary/execution_policy.md",
        "tllos/agent_runtime/execution_boundary/target_registry.md",
        "tllos/agent_runtime/execution_boundary/result_verification.md",
        "tllos/agent_runtime/execution_boundary/schemas/runtime_target.json",
        "tllos/agent_runtime/execution_boundary/schemas/execution_policy.json",
        "tllos/agent_runtime/execution_boundary/schemas/execution_result_validation.json",
        "tllos/agent_runtime/execution_boundary/lifecycle/execution_lifecycle.md",
        "tllos/agent_runtime/execution_boundary/lifecycle/execution_states.json",
    ]
    for file_path in boundary_files:
        if check_file_exists(file_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Execution Boundary Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Execution Boundary Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
