#!/usr/bin/env python3
"""
TLL OS Agent Runtime Validator
验证 Agent Runtime 协议文件的结构完整性。

不依赖外部库，使用内置 json 模块进行基本结构验证。

用法：
    python tools/agent_runtime_validator/validate_agent_runtime.py

退出码：
    0: 全部验证通过
    1: 存在验证失败
"""

import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

VALIDATION_RULES = [
    {
        "name": "boot_protocol.json",
        "path": "tllos/agent_runtime/boot_protocol.json",
        "required_fields": [
            "protocol_name",
            "protocol_version",
            "boot_sequence",
            "principles"
        ],
        "field_types": {
            "protocol_name": str,
            "protocol_version": str,
            "boot_sequence": list,
            "principles": list
        }
    },
    {
        "name": "task_contract.json",
        "path": "tllos/agent_runtime/task_contract.json",
        "required_fields": [
            "contract_name",
            "contract_version",
            "required_fields",
            "validation_rules"
        ],
        "field_types": {
            "contract_name": str,
            "contract_version": str,
            "required_fields": dict,
            "validation_rules": list
        }
    },
    {
        "name": "evidence_record.json",
        "path": "tllos/agent_runtime/evidence_record.json",
        "required_fields": [
            "record_name",
            "record_version",
            "required_fields",
            "validation_rules"
        ],
        "field_types": {
            "record_name": str,
            "record_version": str,
            "required_fields": dict,
            "validation_rules": list
        }
    },
]


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


def validate_structure(data, rule):
    errors = []
    for field in rule["required_fields"]:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    for field, expected_type in rule.get("field_types", {}).items():
        if field in data:
            if not isinstance(data[field], expected_type):
                errors.append(
                    f"Field '{field}' type mismatch: "
                    f"expected {expected_type.__name__}, got {type(data[field]).__name__}"
                )
    return errors


def main():
    print("=" * 60)
    print("TLL OS Agent Runtime Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    for rule in VALIDATION_RULES:
        file_path = rule["path"]
        name = rule["name"]

        parse_ok, parse_result = validate_json_file(file_path)
        if not parse_ok:
            print(f"❌ FAIL: {name}")
            print(f"   Error: {parse_result}")
            all_passed = False
            results.append((name, "FAIL", parse_result))
            continue

        errors = validate_structure(parse_result, rule)
        if errors:
            print(f"❌ FAIL: {name}")
            for err in errors:
                print(f"   - {err}")
            all_passed = False
            results.append((name, "FAIL", "; ".join(errors)))
        else:
            print(f"✅ PASS: {name}")
            results.append((name, "PASS", ""))

    print()
    print("=" * 60)
    if all_passed:
        print("Agent Runtime Validation PASS")
        print()
        for name, status, _ in results:
            print(f"  {name:30s} {status}")
        print()
        sys.exit(0)
    else:
        print("Agent Runtime Validation FAIL")
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
