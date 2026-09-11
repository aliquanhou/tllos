#!/usr/bin/env python3
"""
TLL OS Agent Runtime Seal Validator
统一入口，一次运行验证 Agent Runtime 七层完整性。

七层:
1. Identity Adapter
2. Capability Manager
3. Permission Model
4. Execution Gateway
5. Runtime Adapter
6. Audit Ledger
7. Trust Verification

用法：
    python tools/agent_runtime_validator/validate_agent_runtime_seal.py

退出码：
    0: 七层全部验证通过
    1: 存在验证失败
"""

import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))


def check_file_exists(file_path):
    full_path = os.path.join(PROJECT_ROOT, file_path)
    return os.path.exists(full_path)


def validate_json_file(file_path, required_fields=None):
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

    if required_fields:
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: '{field}'"

    return True, "OK"


def check_layer(name, md_files, json_files):
    """验证单层：md 文件只检查存在，json 文件检查存在+解析+字段"""
    passed = 0
    failed = 0
    errors = []

    for md_file in md_files:
        if check_file_exists(md_file):
            passed += 1
        else:
            errors.append(f"  ❌ Missing MD: {md_file}")
            failed += 1

    for json_file, required_fields in json_files:
        ok, msg = validate_json_file(json_file, required_fields)
        if ok:
            passed += 1
        else:
            errors.append(f"  ❌ {json_file}: {msg}")
            failed += 1

    return passed, failed, errors


def main():
    print("=" * 60)
    print("TLL OS Agent Runtime Seal Validation")
    print("=" * 60)
    print()

    layers = [
        {
            "name": "Layer 1: Identity Adapter",
            "md": ["tllos/agent_runtime/identity/adapter.md"],
            "json": [
                ("tllos/agent_runtime/boot_protocol.json", ["boot_sequence"]),
            ]
        },
        {
            "name": "Layer 2: Capability Manager",
            "md": ["tllos/agent_runtime/capability/manager.md"],
            "json": [
                ("tllos/agent_runtime/capability_declaration.schema.json", None),
            ]
        },
        {
            "name": "Layer 3: Permission Model",
            "md": ["tllos/agent_runtime/permission/permission_model.md"],
            "json": [
                ("tllos/agent_runtime/permission/permission_policy.json", None),
                ("tllos/agent_runtime/permission/permission_schema.json", None),
                ("tllos/agent_runtime/permission/capability_permission_map.json", None),
            ]
        },
        {
            "name": "Layer 4: Execution Gateway",
            "md": ["tllos/agent_runtime/gateway/execution_gateway.md"],
            "json": [
                ("tllos/agent_runtime/gateway/gateway_request.json", None),
                ("tllos/agent_runtime/gateway/gateway_response.json", None),
            ]
        },
        {
            "name": "Layer 5: Runtime Adapter",
            "md": ["tllos/agent_runtime/adapter/runtime_adapter.md"],
            "json": [
                ("tllos/agent_runtime/adapter/runtime_request.json", None),
                ("tllos/agent_runtime/adapter/runtime_result.json", None),
            ]
        },
        {
            "name": "Layer 6: Audit Ledger",
            "md": [
                "tllos/agent_runtime/audit_ledger/README.md",
                "tllos/agent_runtime/audit_ledger/evidence_binding.md",
            ],
            "json": [
                ("tllos/agent_runtime/audit_ledger/audit_event.json", None),
                ("tllos/agent_runtime/audit_ledger/ledger_record.json", None),
            ]
        },
        {
            "name": "Layer 7: Trust Verification",
            "md": [
                "tllos/agent_runtime/trust/README.md",
                "tllos/agent_runtime/trust/trust_chain.md",
            ],
            "json": [
                ("tllos/agent_runtime/trust/trust_verification.json", None),
                ("tllos/agent_runtime/trust/verification_rules.json", None),
                ("tllos/agent_runtime/trust/trust_state.json", None),
            ]
        },
    ]

    total_passed = 0
    total_failed = 0
    layer_results = []

    for layer in layers:
        print(f"--- {layer['name']} ---")
        passed, failed, errors = check_layer(layer["name"], layer["md"], layer["json"])

        if failed == 0:
            print(f"  ✅ PASS ({passed}/{passed})")
        else:
            print(f"  ❌ FAIL ({failed} errors)")
            for err in errors:
                print(err)

        total_passed += passed
        total_failed += failed
        layer_results.append((layer["name"], failed == 0))
        print()

    print("=" * 60)
    if total_failed == 0:
        print("Agent Runtime Seal Validation PASS")
        print(f"  7/7 Layers Verified")
        print(f"  {total_passed} files checked")
        print()
        for name, passed in layer_results:
            print(f"  {name:40s} ✅")
        print()
        sys.exit(0)
    else:
        print("Agent Runtime Seal Validation FAIL")
        print(f"  {total_failed} errors found")
        print()
        for name, passed in layer_results:
            if passed:
                print(f"  {name:40s} ✅")
            else:
                print(f"  {name:40s} ❌")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
