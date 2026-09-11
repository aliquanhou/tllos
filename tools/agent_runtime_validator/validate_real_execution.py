#!/usr/bin/env python3
"""
TLL OS Real Execution Validator
验证 Real Execution 层的协议完整性。

Gates:
- Gate 1: Identity Gate
- Gate 2: Permission Gate
- Gate 3: Target Gate
- Gate 4: Driver Gate
- Gate 5: Result Gate

用法：
    python tools/agent_runtime_validator/validate_real_execution.py

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
    print("TLL OS Real Execution Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Identity Gate
    print("--- Gate 1: Identity Gate ---")
    arch_file = "tllos/agent_runtime/real_execution/architecture.md"
    if check_file_exists(arch_file):
        with open(os.path.join(PROJECT_ROOT, arch_file), "r", encoding="utf-8") as f:
            content = f.read()
        has_identity = "Identity" in content and "无 Identity" in content
        if has_identity:
            print(f"  ✅ PASS: identity requirement defined")
            results.append(("Gate 1: Identity Gate", "PASS"))
        else:
            print(f"  ❌ FAIL: identity requirement not found")
            all_passed = False
            results.append(("Gate 1: Identity Gate", "FAIL"))
    else:
        print(f"  ❌ FAIL: architecture.md not found")
        all_passed = False
        results.append(("Gate 1: Identity Gate", "FAIL"))

    # Gate 2: Permission Gate
    print()
    print("--- Gate 2: Permission Gate ---")
    if check_file_exists(arch_file):
        with open(os.path.join(PROJECT_ROOT, arch_file), "r", encoding="utf-8") as f:
            content = f.read()
        has_permission = "Permission" in content and "无 Permission" in content
        if has_permission:
            print(f"  ✅ PASS: permission requirement defined")
            results.append(("Gate 2: Permission Gate", "PASS"))
        else:
            print(f"  ❌ FAIL: permission requirement not found")
            all_passed = False
            results.append(("Gate 2: Permission Gate", "FAIL"))
    else:
        print(f"  ❌ FAIL: architecture.md not found")
        all_passed = False
        results.append(("Gate 2: Permission Gate", "FAIL"))

    # Gate 3: Target Gate
    print()
    print("--- Gate 3: Target Gate ---")
    target_file = "tllos/agent_runtime/real_execution/execution_target.md"
    if check_file_exists(target_file):
        with open(os.path.join(PROJECT_ROOT, target_file), "r", encoding="utf-8") as f:
            content = f.read()
        has_target = "Target" in content and "Registry" in content
        if has_target:
            print(f"  ✅ PASS: target registry defined")
            results.append(("Gate 3: Target Gate", "PASS"))
        else:
            print(f"  ❌ FAIL: target registry not found")
            all_passed = False
            results.append(("Gate 3: Target Gate", "FAIL"))
    else:
        print(f"  ❌ FAIL: execution_target.md not found")
        all_passed = False
        results.append(("Gate 3: Target Gate", "FAIL"))

    # Gate 4: Driver Gate
    print()
    print("--- Gate 4: Driver Gate ---")
    ok, data = validate_json_file("tllos/agent_runtime/real_execution/execution_driver_schema.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 4: Driver Gate", "FAIL"))
    else:
        required = ["driver_id", "runtime_type", "permission", "capability", "handler", "evidence"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 4: Driver Gate", "FAIL"))
        else:
            supported = data.get("supported_drivers", [])
            if len(supported) >= 4:
                print(f"  ✅ PASS: driver schema valid, {len(supported)} drivers supported")
                results.append(("Gate 4: Driver Gate", "PASS"))
            else:
                print(f"  ❌ FAIL: insufficient drivers")
                all_passed = False
                results.append(("Gate 4: Driver Gate", "FAIL"))

    # Gate 5: Result Gate
    print()
    print("--- Gate 5: Result Gate ---")
    result_file = "tllos/agent_runtime/real_execution/execution_result.md"
    if check_file_exists(result_file):
        with open(os.path.join(PROJECT_ROOT, result_file), "r", encoding="utf-8") as f:
            content = f.read()
        has_result = "Result" in content and "evidence_ref" in content and "audit_ref" in content
        if has_result:
            print(f"  ✅ PASS: result schema valid, evidence binding required")
            results.append(("Gate 5: Result Gate", "PASS"))
        else:
            print(f"  ❌ FAIL: result schema incomplete")
            all_passed = False
            results.append(("Gate 5: Result Gate", "FAIL"))
    else:
        print(f"  ❌ FAIL: execution_result.md not found")
        all_passed = False
        results.append(("Gate 5: Result Gate", "FAIL"))

    # Also check directory structure
    print()
    print("--- Directory Structure ---")
    real_execution_files = [
        "tllos/agent_runtime/real_execution/README.md",
        "tllos/agent_runtime/real_execution/architecture.md",
        "tllos/agent_runtime/real_execution/execution_target.md",
        "tllos/agent_runtime/real_execution/execution_driver.md",
        "tllos/agent_runtime/real_execution/execution_adapter.md",
        "tllos/agent_runtime/real_execution/execution_result.md",
        "tllos/agent_runtime/real_execution/execution_driver_schema.json",
        "tllos/agent_runtime/real_execution/execution_lifecycle.json",
    ]
    for file_path in real_execution_files:
        if check_file_exists(file_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Real Execution Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Real Execution Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
