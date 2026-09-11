#!/usr/bin/env python3
"""
TLL OS Execution Orchestrator Validator
验证 Execution Orchestrator 层的协议完整性。

Gates:
- Gate 1: Execution Plan Schema
- Gate 2: State Transition
- Gate 3: Permission Binding
- Gate 4: Evidence Binding
- Gate 5: Audit Event Binding

用法：
    python tools/agent_runtime_validator/validate_execution_orchestrator.py

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
    print("TLL OS Execution Orchestrator Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Execution Plan Schema
    print("--- Gate 1: Execution Plan Schema ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_orchestrator/execution_plan.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 1: Execution Plan Schema", "FAIL"))
    else:
        required = ["plan_id", "agent_id", "task_id", "steps", "required_permissions", "evidence_required", "audit_required"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 1: Execution Plan Schema", "FAIL"))
        else:
            print(f"  ✅ PASS: all required fields present")
            results.append(("Gate 1: Execution Plan Schema", "PASS"))

    # Gate 2: State Transition
    print()
    print("--- Gate 2: State Transition ---")
    sm_file = "tllos/agent_runtime/execution_orchestrator/orchestration_state_machine.md"
    if check_file_exists(sm_file):
        print(f"  ✅ PASS: state machine defined")
        results.append(("Gate 2: State Transition", "PASS"))
    else:
        print(f"  ❌ FAIL: state machine file not found")
        all_passed = False
        results.append(("Gate 2: State Transition", "FAIL"))

    # Gate 3: Permission Binding
    print()
    print("--- Gate 3: Permission Binding ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_orchestrator/execution_plan.json")
    if ok and "required_permissions" in data.get("required_fields", []):
        print(f"  ✅ PASS: required_permissions is required")
        results.append(("Gate 3: Permission Binding", "PASS"))
    else:
        print(f"  ❌ FAIL: required_permissions not required")
        all_passed = False
        results.append(("Gate 3: Permission Binding", "FAIL"))

    # Gate 4: Evidence Binding
    print()
    print("--- Gate 4: Evidence Binding ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_orchestrator/execution_orchestration_evidence.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 4: Evidence Binding", "FAIL"))
    else:
        required = ["orchestration_id", "execution_plan", "steps", "evidence_chain", "audit_events"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 4: Evidence Binding", "FAIL"))
        else:
            print(f"  ✅ PASS: evidence_chain is required")
            results.append(("Gate 4: Evidence Binding", "PASS"))

    # Gate 5: Audit Event Binding
    print()
    print("--- Gate 5: Audit Event Binding ---")
    ok, audit_data = validate_json_file("tllos/agent_runtime/audit_ledger/audit_event.json")
    if not ok:
        print(f"  ❌ FAIL: {audit_data}")
        all_passed = False
        results.append(("Gate 5: Audit Event Binding", "FAIL"))
    else:
        required_events = ["ORCHESTRATION_CREATED", "ORCHESTRATION_APPROVED", "ORCHESTRATION_STARTED", "ORCHESTRATION_COMPLETED", "ORCHESTRATION_FAILED"]
        existing_events = audit_data.get("event_types", [])
        missing = [e for e in required_events if e not in existing_events]
        if missing:
            print(f"  ❌ FAIL: missing audit events: {missing}")
            all_passed = False
            results.append(("Gate 5: Audit Event Binding", "FAIL"))
        else:
            print(f"  ✅ PASS: all required audit events present")
            results.append(("Gate 5: Audit Event Binding", "PASS"))

    # Also check directory structure
    print()
    print("--- Directory Structure ---")
    orchestrator_files = [
        "tllos/agent_runtime/execution_orchestrator/README.md",
        "tllos/agent_runtime/execution_orchestrator/architecture.md",
        "tllos/agent_runtime/execution_orchestrator/orchestration_model.md",
        "tllos/agent_runtime/execution_orchestrator/execution_plan.json",
        "tllos/agent_runtime/execution_orchestrator/orchestration_state_machine.md",
        "tllos/agent_runtime/execution_orchestrator/execution_orchestration_evidence.json",
    ]
    for file_path in orchestrator_files:
        if check_file_exists(file_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Execution Orchestrator Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Execution Orchestrator Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
