#!/usr/bin/env python3
"""
TLL OS Driver Registry Validator
验证 Driver Registry 的协议完整性。

Gates:
- Gate 1: Schema
- Gate 2: Registry
- Gate 3: Permission
- Gate 4: Lifecycle
- Gate 5: Evidence

用法：
    python tools/agent_runtime_validator/validate_driver_registry.py

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
    print("TLL OS Driver Registry Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Schema
    print("--- Gate 1: Schema ---")
    ok, data = validate_json_file("tllos/agent_runtime/driver/driver_metadata_schema.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 1: Schema", "FAIL"))
    else:
        required = ["driver_id", "runtime_type", "capability", "permission", "handler", "evidence", "status"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 1: Schema", "FAIL"))
        else:
            print(f"  ✅ PASS: all required fields present")
            results.append(("Gate 1: Schema", "PASS"))

    # Gate 2: Registry
    print()
    print("--- Gate 2: Registry ---")
    ok, data = validate_json_file("tllos/agent_runtime/driver/driver_registry.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 2: Registry", "FAIL"))
    else:
        drivers = data.get("drivers", [])
        if len(drivers) >= 4:
            print(f"  ✅ PASS: {len(drivers)} drivers registered")
            results.append(("Gate 2: Registry", "PASS"))
        else:
            print(f"  ❌ FAIL: insufficient drivers")
            all_passed = False
            results.append(("Gate 2: Registry", "FAIL"))

    # Gate 3: Permission
    print()
    print("--- Gate 3: Permission ---")
    ok, data = validate_json_file("tllos/agent_runtime/driver/driver_capability_mapping.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 3: Permission", "FAIL"))
    else:
        mappings = data.get("mappings", [])
        all_have_permission = all("permission" in m for m in mappings)
        all_have_capability = all("capability" in m for m in mappings)
        if all_have_permission and all_have_capability and len(mappings) >= 4:
            print(f"  ✅ PASS: permission-capability mapping valid, {len(mappings)} entries")
            results.append(("Gate 3: Permission", "PASS"))
        else:
            print(f"  ❌ FAIL: permission mapping incomplete")
            all_passed = False
            results.append(("Gate 3: Permission", "FAIL"))

    # Gate 4: Lifecycle
    print()
    print("--- Gate 4: Lifecycle ---")
    ok, data = validate_json_file("tllos/agent_runtime/driver/driver_lifecycle.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 4: Lifecycle", "FAIL"))
    else:
        states = data.get("states", [])
        required_states = ["REGISTERED", "VALIDATING", "AUTHORIZED", "READY", "EXECUTING", "COMPLETED", "FAILED", "DISABLED"]
        missing = [s for s in required_states if s not in states]
        if missing:
            print(f"  ❌ FAIL: missing states: {missing}")
            all_passed = False
            results.append(("Gate 4: Lifecycle", "FAIL"))
        else:
            print(f"  ✅ PASS: lifecycle valid, {len(states)} states")
            results.append(("Gate 4: Lifecycle", "PASS"))

    # Gate 5: Evidence
    print()
    print("--- Gate 5: Evidence ---")
    ok, data = validate_json_file("tllos/agent_runtime/driver/driver_registry.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 5: Evidence", "FAIL"))
    else:
        drivers = data.get("drivers", [])
        all_have_evidence = all("evidence" in d for d in drivers)
        if all_have_evidence and len(drivers) >= 4:
            print(f"  ✅ PASS: all drivers have evidence reference")
            results.append(("Gate 5: Evidence", "PASS"))
        else:
            print(f"  ❌ FAIL: missing evidence references")
            all_passed = False
            results.append(("Gate 5: Evidence", "FAIL"))

    # Also check directory structure
    print()
    print("--- Directory Structure ---")
    driver_files = [
        "tllos/agent_runtime/driver/README.md",
        "tllos/agent_runtime/driver/driver_interface.md",
        "tllos/agent_runtime/driver/driver_metadata_schema.json",
        "tllos/agent_runtime/driver/driver_lifecycle.json",
        "tllos/agent_runtime/driver/driver_registry.json",
        "tllos/agent_runtime/driver/driver_capability_mapping.json",
        "tllos/agent_runtime/driver/driver_validation_gate.md",
    ]
    for file_path in driver_files:
        if check_file_exists(file_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Driver Registry Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Driver Registry Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
