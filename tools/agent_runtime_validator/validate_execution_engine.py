#!/usr/bin/env python3
"""
TLL OS Execution Engine Validator
验证 Execution Engine 的协议完整性。

Test Cases:
- Test-25: 合法 Execution Context -> PASS
- Test-26: 缺少 permission -> REJECT
- Test-27: 缺少 evidence_required -> REJECT
- Test-28: 非法状态跳转 -> REJECT
- Test-29: 伪造 agent_id -> REJECT

用法：
    python tools/agent_runtime_validator/validate_execution_engine.py

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


def validate_execution_context(context, known_agents=None):
    """验证 Execution Context 是否合法"""
    errors = []

    # Required fields
    required = ["execution_id", "agent_id", "task_id", "capability", "permission", "evidence_required", "status"]
    for field in required:
        if field not in context:
            errors.append(f"Missing required field: {field}")

    # agent_id must be in known_agents (if provided)
    if known_agents and "agent_id" in context:
        if context["agent_id"] not in known_agents:
            errors.append(f"Unknown agent_id: {context['agent_id']}")

    # evidence_required must be boolean
    if "evidence_required" in context and not isinstance(context["evidence_required"], bool):
        errors.append("evidence_required must be boolean")

    return errors


def validate_state_transition(current_state, target_state, valid_transitions):
    """验证状态转换是否合法"""
    if current_state not in valid_transitions:
        return False, f"Unknown current state: {current_state}"
    if target_state not in valid_transitions[current_state]:
        return False, f"Illegal transition: {current_state} -> {target_state}"
    return True, "OK"


def main():
    print("=" * 60)
    print("TLL OS Execution Engine Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Test-25: 合法 Execution Context
    print("--- Test-25: 合法 Execution Context ---")
    valid_context = {
        "execution_id": "exec-001",
        "agent_id": "doubao-a",
        "task_id": "task-001",
        "capability": "write_evidence",
        "permission": "write:evidence",
        "evidence_required": True,
        "status": "CREATED"
    }
    errors = validate_execution_context(valid_context, known_agents=["doubao-a", "doubao-b"])
    if not errors:
        print("  ✅ PASS")
        results.append(("Test-25: 合法 Execution Context", "PASS"))
    else:
        print(f"  ❌ FAIL: {errors}")
        all_passed = False
        results.append(("Test-25: 合法 Execution Context", "FAIL"))

    # Test-26: 缺少 permission
    print()
    print("--- Test-26: 缺少 permission ---")
    no_permission = {
        "execution_id": "exec-002",
        "agent_id": "doubao-a",
        "task_id": "task-002",
        "capability": "write_evidence",
        "evidence_required": True,
        "status": "CREATED"
    }
    errors = validate_execution_context(no_permission, known_agents=["doubao-a"])
    if any("permission" in err for err in errors):
        print("  ✅ PASS (REJECTED as expected)")
        results.append(("Test-26: 缺少 permission", "PASS"))
    else:
        print(f"  ❌ FAIL: should have been rejected")
        all_passed = False
        results.append(("Test-26: 缺少 permission", "FAIL"))

    # Test-27: 缺少 evidence_required
    print()
    print("--- Test-27: 缺少 evidence_required ---")
    no_evidence = {
        "execution_id": "exec-003",
        "agent_id": "doubao-a",
        "task_id": "task-003",
        "capability": "write_evidence",
        "permission": "write:evidence",
        "status": "CREATED"
    }
    errors = validate_execution_context(no_evidence, known_agents=["doubao-a"])
    if any("evidence_required" in err for err in errors):
        print("  ✅ PASS (REJECTED as expected)")
        results.append(("Test-27: 缺少 evidence_required", "PASS"))
    else:
        print(f"  ❌ FAIL: should have been rejected")
        all_passed = False
        results.append(("Test-27: 缺少 evidence_required", "FAIL"))

    # Test-28: 非法状态跳转
    print()
    print("--- Test-28: 非法状态跳转 ---")
    valid_transitions = {
        "CREATED": ["AUTHORIZED", "REJECTED"],
        "AUTHORIZED": ["RUNNING", "REJECTED"],
        "RUNNING": ["COMPLETED", "FAILED", "AUDIT_REQUIRED"],
        "COMPLETED": [],
        "REJECTED": [],
        "FAILED": [],
        "AUDIT_REQUIRED": ["COMPLETED", "FAILED"]
    }
    # Illegal: CREATED -> RUNNING
    ok, msg = validate_state_transition("CREATED", "RUNNING", valid_transitions)
    if not ok:
        print("  ✅ PASS (CREATED -> RUNNING rejected as expected)")
        results.append(("Test-28: 非法状态跳转", "PASS"))
    else:
        print(f"  ❌ FAIL: CREATED -> RUNNING should have been rejected")
        all_passed = False
        results.append(("Test-28: 非法状态跳转", "FAIL"))

    # Test-29: 伪造 agent_id
    print()
    print("--- Test-29: 伪造 agent_id ---")
    unknown_agent = {
        "execution_id": "exec-004",
        "agent_id": "unknown-agent",
        "task_id": "task-004",
        "capability": "write_evidence",
        "permission": "write:evidence",
        "evidence_required": True,
        "status": "CREATED"
    }
    errors = validate_execution_context(unknown_agent, known_agents=["doubao-a", "doubao-b"])
    if any("Unknown agent_id" in err for err in errors):
        print("  ✅ PASS (REJECTED as expected)")
        results.append(("Test-29: 伪造 agent_id", "PASS"))
    else:
        print(f"  ❌ FAIL: should have been rejected")
        all_passed = False
        results.append(("Test-29: 伪造 agent_id", "FAIL"))

    # Also validate files exist
    print()
    print("--- File Validation ---")
    files_to_check = [
        "tllos/agent_runtime/execution_engine/README.md",
        "tllos/agent_runtime/execution_engine/architecture.md",
        "tllos/agent_runtime/execution_engine/execution_context.md",
        "tllos/agent_runtime/execution_engine/context_schema.json",
        "tllos/agent_runtime/execution_engine/execution_request.json",
        "tllos/agent_runtime/execution_engine/execution_response.json",
    ]
    for file_path in files_to_check:
        full_path = os.path.join(PROJECT_ROOT, file_path)
        if os.path.exists(full_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Execution Engine Validation PASS")
        print(f"  5/5 Tests Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Execution Engine Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
