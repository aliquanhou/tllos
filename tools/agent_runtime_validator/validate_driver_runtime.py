#!/usr/bin/env python3
"""
TLL OS Driver Runtime Validator
验证 Driver Runtime 的协议完整性。

Gates:
- Gate 1: Interface
- Gate 2: Context
- Gate 3: Lifecycle
- Gate 4: Evidence
- Gate 5: Audit

用法：
    python tools/agent_runtime_validator/validate_driver_runtime.py

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
    print("TLL OS Driver Runtime Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Interface
    print("--- Gate 1: Interface ---")
    if check_file_exists("tllos/agent_runtime/driver_runtime/runtime_interface.md"):
        print(f"  ✅ PASS: runtime_interface.md exists")
        results.append(("Gate 1: Interface", "PASS"))
    else:
        print(f"  ❌ FAIL: runtime_interface.md not found")
        all_passed = False
        results.append(("Gate 1: Interface", "FAIL"))

    # Gate 2: Context
    print()
    print("--- Gate 2: Context ---")
    ok, data = validate_json_file("tllos/agent_runtime/driver_runtime/driver_context.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 2: Context", "FAIL"))
    else:
        required = ["execution_id", "agent_identity", "capability", "permission", "runtime_target", "evidence_reference", "governance_reference"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 2: Context", "FAIL"))
        else:
            print(f"  ✅ PASS: all required context fields present")
            results.append(("Gate 2: Context", "PASS"))

    # Gate 3: Lifecycle
    print()
    print("--- Gate 3: Lifecycle ---")
    ok, data = validate_json_file("tllos/agent_runtime/driver/driver_lifecycle.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 3: Lifecycle", "FAIL"))
    else:
        states = data.get("states", [])
        required_states = ["REGISTERED", "VALIDATING", "AUTHORIZED", "READY", "INITIALIZED", "PREPARED", "EXECUTING", "COLLECTING", "FINALIZED", "COMPLETED", "FAILED", "DISABLED"]
        missing = [s for s in required_states if s not in states]
        if missing:
            print(f"  ❌ FAIL: missing states: {missing}")
            all_passed = False
            results.append(("Gate 3: Lifecycle", "FAIL"))
        else:
            print(f"  ✅ PASS: lifecycle valid, {len(states)} states")
            results.append(("Gate 3: Lifecycle", "PASS"))

    # Gate 4: Evidence
    print()
    print("--- Gate 4: Evidence ---")
    ok, data = validate_json_file("tllos/agent_runtime/driver_runtime/driver_result.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 4: Evidence", "FAIL"))
    else:
        required = ["status", "output", "error", "execution_time", "evidence", "audit_reference"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required result fields: {missing}")
            all_passed = False
            results.append(("Gate 4: Evidence", "FAIL"))
        else:
            print(f"  ✅ PASS: result evidence fields present")
            results.append(("Gate 4: Evidence", "PASS"))

    # Gate 5: Audit
    print()
    print("--- Gate 5: Audit ---")
    ok, data = validate_json_file("tllos/agent_runtime/audit_ledger/audit_event.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 5: Audit", "FAIL"))
    else:
        event_types = data.get("event_types", [])
        required_events = ["DRIVER_INITIALIZED", "DRIVER_PREPARED", "DRIVER_EXECUTED", "DRIVER_RESULT_COLLECTED", "DRIVER_FINALIZED"]
        missing = [e for e in required_events if e not in event_types]
        if missing:
            print(f"  ❌ FAIL: missing audit events: {missing}")
            all_passed = False
            results.append(("Gate 5: Audit", "FAIL"))
        else:
            print(f"  ✅ PASS: audit events present, {len(event_types)} total")
            results.append(("Gate 5: Audit", "PASS"))

    # Also check directory structure
    print()
    print("--- Directory Structure ---")
    runtime_files = [
        "tllos/agent_runtime/driver_runtime/README.md",
        "tllos/agent_runtime/driver_runtime/architecture.md",
        "tllos/agent_runtime/driver_runtime/runtime_interface.md",
        "tllos/agent_runtime/driver_runtime/driver_context.json",
        "tllos/agent_runtime/driver_runtime/driver_result.json",
        "tllos/agent_runtime/driver_runtime/driver_runtime_manager.md",
        "tllos/agent_runtime/driver_runtime/driver_adapter/README.md",
        "tllos/agent_runtime/driver_runtime/driver_adapter/mock_driver.md",
    ]
    for file_path in runtime_files:
        if check_file_exists(file_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Driver Runtime Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Driver Runtime Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
