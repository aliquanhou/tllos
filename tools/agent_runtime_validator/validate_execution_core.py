#!/usr/bin/env python3
"""
TLL OS Execution Core Validator
验证 Execution Engine Core 的协议完整性。

Gates:
- Gate 1: Execution Context
- Gate 2: State Machine
- Gate 3: Permission Binding
- Gate 4: Audit Binding
- Gate 5: Runtime Adapter Boundary

用法：
    python tools/agent_runtime_validator/validate_execution_core.py

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
    print("TLL OS Execution Core Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Execution Context
    print("--- Gate 1: Execution Context ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_engine/core/context_runtime.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 1: Execution Context", "FAIL"))
    else:
        required = ["execution_id", "agent_identity", "capability_id", "permission_set", "runtime_target", "audit_reference", "evidence_reference", "created_at"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 1: Execution Context", "FAIL"))
        else:
            print(f"  ✅ PASS")
            results.append(("Gate 1: Execution Context", "PASS"))

    # Gate 2: State Machine
    print()
    print("--- Gate 2: State Machine ---")
    state_machine_file = "tllos/agent_runtime/execution_engine/core/execution_state_machine.md"
    if check_file_exists(state_machine_file):
        print(f"  ✅ PASS: state machine defined")
        results.append(("Gate 2: State Machine", "PASS"))
    else:
        print(f"  ❌ FAIL: state machine file not found")
        all_passed = False
        results.append(("Gate 2: State Machine", "FAIL"))

    # Gate 3: Permission Binding
    print()
    print("--- Gate 3: Permission Binding ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_engine/core/context_runtime.json")
    if ok and "permission_set" in data.get("required_fields", []):
        print(f"  ✅ PASS: permission_set required")
        results.append(("Gate 3: Permission Binding", "PASS"))
    else:
        print(f"  ❌ FAIL: permission_set not required")
        all_passed = False
        results.append(("Gate 3: Permission Binding", "FAIL"))

    # Gate 4: Audit Binding
    print()
    print("--- Gate 4: Audit Binding ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_engine/core/context_runtime.json")
    if ok and "audit_reference" in data.get("required_fields", []):
        print(f"  ✅ PASS: audit_reference required")
        results.append(("Gate 4: Audit Binding", "PASS"))
    else:
        print(f"  ❌ FAIL: audit_reference not required")
        all_passed = False
        results.append(("Gate 4: Audit Binding", "FAIL"))

    # Gate 5: Runtime Adapter Boundary
    print()
    print("--- Gate 5: Runtime Adapter Boundary ---")
    adapter_file = "tllos/agent_runtime/adapter/runtime_adapter.md"
    if check_file_exists(adapter_file):
        # Check if Execution Engine Bridge section exists
        full_path = os.path.join(PROJECT_ROOT, adapter_file)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "Execution Engine Bridge" in content:
            print(f"  ✅ PASS: Execution Engine Bridge defined")
            results.append(("Gate 5: Runtime Adapter Boundary", "PASS"))
        else:
            print(f"  ❌ FAIL: Execution Engine Bridge not found")
            all_passed = False
            results.append(("Gate 5: Runtime Adapter Boundary", "FAIL"))
    else:
        print(f"  ❌ FAIL: adapter file not found")
        all_passed = False
        results.append(("Gate 5: Runtime Adapter Boundary", "FAIL"))

    # Also check core files exist
    print()
    print("--- Core Files ---")
    core_files = [
        "tllos/agent_runtime/execution_engine/core/engine_core.md",
        "tllos/agent_runtime/execution_engine/core/execution_state_machine.md",
        "tllos/agent_runtime/execution_engine/core/context_runtime.json",
        "tllos/agent_runtime/execution_engine/core/dispatcher.md",
    ]
    for file_path in core_files:
        if check_file_exists(file_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Execution Core Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Execution Core Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
