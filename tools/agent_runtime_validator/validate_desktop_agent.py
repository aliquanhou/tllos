#!/usr/bin/env python3
"""
TLL OS Desktop Agent Validator
验证 Desktop Agent 的协议完整性。

Gates:
- Gate 1: Capability
- Gate 2: Permission
- Gate 3: Lifecycle
- Gate 4: Evidence
- Gate 5: Audit

用法：
    python tools/agent_runtime_validator/validate_desktop_agent.py

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
    print("TLL OS Desktop Agent Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Capability
    print("--- Gate 1: Capability ---")
    ok, data = validate_json_file("tllos/agent_runtime/desktop_agent/desktop_capability.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 1: Capability", "FAIL"))
    else:
        capabilities = data.get("capabilities", [])
        required_fields = ["capability_id", "permission", "risk_level", "evidence_required"]
        all_valid = all(all(f in c for f in required_fields) for c in capabilities)
        if all_valid and len(capabilities) >= 7:
            print(f"  ✅ PASS: {len(capabilities)} capabilities defined")
            results.append(("Gate 1: Capability", "PASS"))
        else:
            print(f"  ❌ FAIL: capability fields incomplete")
            all_passed = False
            results.append(("Gate 1: Capability", "FAIL"))

    # Gate 2: Permission
    print()
    print("--- Gate 2: Permission ---")
    ok, data = validate_json_file("tllos/agent_runtime/desktop_agent/desktop_action.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 2: Permission", "FAIL"))
    else:
        required = ["action_id", "capability", "target", "parameters", "permission", "evidence"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 2: Permission", "FAIL"))
        else:
            print(f"  ✅ PASS: all permission fields present")
            results.append(("Gate 2: Permission", "PASS"))

    # Gate 3: Lifecycle
    print()
    print("--- Gate 3: Lifecycle ---")
    ok, data = validate_json_file("tllos/agent_runtime/desktop_agent/lifecycle.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 3: Lifecycle", "FAIL"))
    else:
        states = data.get("states", [])
        required_states = ["REQUESTED", "VALIDATING", "AUTHORIZED", "PREPARING", "EXECUTING", "OBSERVING", "COMPLETED", "FAILED", "ROLLBACK"]
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
    ok, data = validate_json_file("tllos/agent_runtime/desktop_agent/desktop_context.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 4: Evidence", "FAIL"))
    else:
        required = ["os", "device", "window", "application", "session", "user", "timestamp"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing context fields: {missing}")
            all_passed = False
            results.append(("Gate 4: Evidence", "FAIL"))
        else:
            print(f"  ✅ PASS: context evidence fields present")
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
        required_events = ["DESKTOP_ACTION_REQUESTED", "DESKTOP_ACTION_APPROVED", "DESKTOP_ACTION_STARTED", "DESKTOP_ACTION_COMPLETED", "DESKTOP_ACTION_FAILED"]
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
    desktop_files = [
        "tllos/agent_runtime/desktop_agent/architecture.md",
        "tllos/agent_runtime/desktop_agent/desktop_capability.json",
        "tllos/agent_runtime/desktop_agent/desktop_context.json",
        "tllos/agent_runtime/desktop_agent/desktop_action.json",
        "tllos/agent_runtime/desktop_agent/lifecycle.json",
        "tllos/agent_runtime/desktop_agent/driver/screen_driver.md",
        "tllos/agent_runtime/desktop_agent/driver/mouse_driver.md",
        "tllos/agent_runtime/desktop_agent/driver/keyboard_driver.md",
        "tllos/agent_runtime/desktop_agent/driver/window_driver.md",
        "tllos/agent_runtime/desktop_agent/driver/process_driver.md",
        "tllos/agent_runtime/desktop_agent/driver/file_driver.md",
        "tllos/agent_runtime/desktop_agent/safety/safety_layer.md",
    ]
    for file_path in desktop_files:
        if check_file_exists(file_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Desktop Agent Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Desktop Agent Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
