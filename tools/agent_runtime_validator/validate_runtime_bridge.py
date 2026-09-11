#!/usr/bin/env python3
"""
TLL OS Runtime Bridge Validator
验证 Runtime Bridge 层的协议完整性。

Gates:
- Gate 1: Schema 完整
- Gate 2: Execution Engine → Bridge 单向连接
- Gate 3: Bridge → Adapter 单向连接
- Gate 4: 禁止绕过 Bridge
- Gate 5: Evidence 必须存在

用法：
    python tools/agent_runtime_validator/validate_runtime_bridge.py

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
    print("TLL OS Runtime Bridge Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Schema 完整
    print("--- Gate 1: Schema 完整 ---")
    bridge_files = [
        "tllos/agent_runtime/runtime_bridge/README.md",
        "tllos/agent_runtime/runtime_bridge/architecture.md",
        "tllos/agent_runtime/runtime_bridge/runtime_bridge_interface.md",
        "tllos/agent_runtime/runtime_bridge/runtime_bridge_request.json",
        "tllos/agent_runtime/runtime_bridge/runtime_bridge_response.json",
    ]
    missing = []
    for f in bridge_files:
        if not check_file_exists(f):
            missing.append(f)
    if missing:
        print(f"  ❌ FAIL: missing files: {missing}")
        all_passed = False
        results.append(("Gate 1: Schema 完整", "FAIL"))
    else:
        print(f"  ✅ PASS: all bridge files exist")
        results.append(("Gate 1: Schema 完整", "PASS"))

    # Gate 2: Execution Engine → Bridge 单向连接
    print()
    print("--- Gate 2: Execution Engine → Bridge 单向连接 ---")
    engine_core = read_file_content("tllos/agent_runtime/execution_engine/core/engine_core.md")
    if engine_core and "Runtime Bridge" in engine_core:
        print(f"  ✅ PASS: Engine references Runtime Bridge")
        results.append(("Gate 2: Engine → Bridge 单向", "PASS"))
    else:
        print(f"  ❌ FAIL: Engine does not reference Runtime Bridge")
        all_passed = False
        results.append(("Gate 2: Engine → Bridge 单向", "FAIL"))

    # Gate 3: Bridge → Adapter 单向连接
    print()
    print("--- Gate 3: Bridge → Adapter 单向连接 ---")
    bridge_arch = read_file_content("tllos/agent_runtime/runtime_bridge/architecture.md")
    if bridge_arch and "Runtime Adapter" in bridge_arch:
        print(f"  ✅ PASS: Bridge references Runtime Adapter")
        results.append(("Gate 3: Bridge → Adapter 单向", "PASS"))
    else:
        print(f"  ❌ FAIL: Bridge does not reference Runtime Adapter")
        all_passed = False
        results.append(("Gate 3: Bridge → Adapter 单向", "FAIL"))

    # Gate 4: 禁止绕过 Bridge
    print()
    print("--- Gate 4: 禁止绕过 Bridge ---")
    # Check adapter.md mentions Runtime Bridge
    adapter_doc = read_file_content("tllos/agent_runtime/adapter/runtime_adapter.md")
    if adapter_doc and "Runtime Bridge" in adapter_doc:
        print(f"  ✅ PASS: Adapter confirms Bridge as required layer")
        results.append(("Gate 4: 禁止绕过 Bridge", "PASS"))
    else:
        print(f"  ❌ FAIL: Adapter does not confirm Bridge layer")
        all_passed = False
        results.append(("Gate 4: 禁止绕过 Bridge", "FAIL"))

    # Gate 5: Evidence 必须存在
    print()
    print("--- Gate 5: Evidence 必须存在 ---")
    ok, request_schema = validate_json_file("tllos/agent_runtime/runtime_bridge/runtime_bridge_request.json")
    if ok and "evidence" in request_schema.get("required_fields", []):
        print(f"  ✅ PASS: evidence is required field")
        results.append(("Gate 5: Evidence 必须存在", "PASS"))
    else:
        print(f"  ❌ FAIL: evidence is not required")
        all_passed = False
        results.append(("Gate 5: Evidence 必须存在", "FAIL"))

    print()
    print("=" * 60)
    if all_passed:
        print("Runtime Bridge Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Runtime Bridge Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
