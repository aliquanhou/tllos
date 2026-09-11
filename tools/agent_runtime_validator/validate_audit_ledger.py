#!/usr/bin/env python3
"""
TLL OS Audit Ledger Validator
验证 Audit Ledger 协议文件的结构完整性和证据绑定规则。

不依赖外部库，使用内置 json 模块进行基本结构验证。

用法：
    python tools/agent_runtime_validator/validate_audit_ledger.py

退出码：
    0: 全部验证通过
    1: 存在验证失败
"""

import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

VALID_EVENT_TYPES = [
    "AgentRegistered",
    "CapabilityDeclared",
    "PermissionRequested",
    "PermissionGranted",
    "PermissionDenied",
    "TaskCreated",
    "ExecutionRequested",
    "ExecutionCompleted",
    "ExecutionFailed",
    "EvidenceGenerated",
    "TaskRejected",
    "AuditReviewed",
    "EXECUTION_CREATED",
    "EXECUTION_VALIDATING",
    "EXECUTION_VALIDATED",
    "EXECUTION_AUTHORIZED",
    "EXECUTION_STARTED",
    "EXECUTION_COMPLETED",
    "EXECUTION_FAILED",
    "EXECUTION_REJECTED",
    "RUNTIME_BRIDGE_CREATED",
    "RUNTIME_BRIDGE_VALIDATED",
    "RUNTIME_REQUEST_FORWARDED",
    "RUNTIME_RESPONSE_RECEIVED"
]

VALID_STATUSES = ["SUCCESS", "FAILURE", "PENDING", "REJECTED"]


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


def validate_event_file(data, name):
    errors = []

    required_fields = ["event_name", "event_version", "required_fields", "validation_rules"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if "event_types" in data:
        for et in data["event_types"]:
            if et not in VALID_EVENT_TYPES:
                errors.append(f"Unknown event type: {et}")

    return errors


def validate_ledger_file(data, name):
    errors = []

    required_fields = ["record_name", "record_version", "required_fields", "validation_rules"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    return errors


def validate_event_example(data):
    """
    验证 example 中的事件是否符合规则：
    1. ExecutionCompleted 必须有 evidence_ref
    2. ExecutionRequested 必须有 permission
    """
    errors = []

    example = data.get("example", {})
    if not example:
        return errors

    event_type = example.get("event_type")

    if event_type == "ExecutionCompleted":
        if not example.get("evidence_ref"):
            errors.append("ExecutionCompleted example missing evidence_ref")

    if event_type == "ExecutionRequested":
        if not example.get("permission"):
            errors.append("ExecutionRequested example missing permission")

    return errors


def main():
    print("=" * 60)
    print("TLL OS Audit Ledger Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # 1. audit_event.json
    print("--- 1. Audit Event ---")
    parse_ok, result = validate_json_file("tllos/agent_runtime/audit_ledger/audit_event.json")
    if not parse_ok:
        print(f"❌ FAIL: audit_event.json")
        print(f"   Error: {result}")
        all_passed = False
        results.append(("audit_event.json", "FAIL", result))
    else:
        errors = validate_event_file(result, "audit_event.json")
        errors += validate_event_example(result)
        if errors:
            print(f"❌ FAIL: audit_event.json")
            for err in errors:
                print(f"   - {err}")
            all_passed = False
            results.append(("audit_event.json", "FAIL", "; ".join(errors)))
        else:
            print(f"✅ PASS: audit_event.json")
            results.append(("audit_event.json", "PASS", ""))

    # 2. ledger_record.json
    print()
    print("--- 2. Ledger Record ---")
    parse_ok, result = validate_json_file("tllos/agent_runtime/audit_ledger/ledger_record.json")
    if not parse_ok:
        print(f"❌ FAIL: ledger_record.json")
        print(f"   Error: {result}")
        all_passed = False
        results.append(("ledger_record.json", "FAIL", result))
    else:
        errors = validate_ledger_file(result, "ledger_record.json")
        if errors:
            print(f"❌ FAIL: ledger_record.json")
            for err in errors:
                print(f"   - {err}")
            all_passed = False
            results.append(("ledger_record.json", "FAIL", "; ".join(errors)))
        else:
            print(f"✅ PASS: ledger_record.json")
            results.append(("ledger_record.json", "PASS", ""))

    # 3. Evidence Binding Check
    print()
    print("--- 3. Evidence Binding ---")
    binding_path = "tllos/agent_runtime/audit_ledger/evidence_binding.md"
    if os.path.exists(os.path.join(PROJECT_ROOT, binding_path)):
        print(f"✅ PASS: evidence_binding.md exists")
        results.append(("evidence_binding.md", "PASS", ""))
    else:
        print(f"❌ FAIL: evidence_binding.md not found")
        all_passed = False
        results.append(("evidence_binding.md", "FAIL", "file not found"))

    print()
    print("=" * 60)
    if all_passed:
        print("Audit Ledger Validation PASS")
        print()
        for name, status, _ in results:
            print(f"  {name:30s} {status}")
        print()
        sys.exit(0)
    else:
        print("Audit Ledger Validation FAIL")
        print()
        for name, status, err in results:
            if status == "PASS":
                print(f"  {name:30s} {status}")
            else:
                print(f"  {name:30s} {status} ({err})")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
