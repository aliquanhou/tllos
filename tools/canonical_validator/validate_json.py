#!/usr/bin/env python3
"""
TLL OS Canonical Validator
验证 Canonical Layer JSON 文件的结构完整性。

不依赖外部库（jsonschema），使用内置 json 模块进行基本结构验证。
未来如果需要完整 JSON Schema 验证，可以升级为使用 jsonschema 库。

用法：
    python validate_json.py

退出码：
    0: 全部验证通过
    1: 存在验证失败
"""

import json
import sys
import os

# 项目根目录（脚本在 tools/canonical_validator/ 下）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

# 定义验证规则：(文件路径, 必需字段列表, 必需字段类型)
VALIDATION_RULES = [
    {
        "name": "genesis.json",
        "path": "tllos/identity/genesis.json",
        "required_fields": [
            "genesis_version",
            "genesis_date",
            "os_name",
            "os_full_name",
            "os_tagline",
            "os_description",
            "language_name",
            "identity_principles",
            "architecture_vision",
            "current_status",
            "truth_declaration"
        ],
        "field_types": {
            "os_name": str,
            "os_full_name": str,
            "genesis_version": str,
            "identity_principles": list,
        }
    },
    {
        "name": "canonical_manifest.json",
        "path": "tllos/identity/canonical_manifest.json",
        "required_fields": [
            "manifest_version",
            "manifest_date",
            "protocol_version_binding",
            "integrity_algorithm",
            "files"
        ],
        "field_types": {
            "protocol_version_binding": dict,
            "files": dict,
            "integrity_algorithm": str,
        }
    },
    {
        "name": "agent_capability.json",
        "path": "tllos/agents/agent_capability.json",
        "required_fields": [
            "capability_protocol_version",
            "agent_registry",
            "capabilities_provided_by_tllos",
            "capabilities_required_from_agents",
            "current_capability_boundaries"
        ],
        "field_types": {
            "agent_registry": dict,
            "current_capability_boundaries": dict,
        }
    },
    {
        "name": "evidence_index.json",
        "path": "tllos/truth/evidence_index.json",
        "required_fields": [
            "index_version",
            "index_date",
            "phases"
        ],
        "field_types": {
            "phases": list,
        }
    },
]


def validate_json_file(file_path):
    """验证单个 JSON 文件：可以 parse + 必需字段存在"""
    full_path = os.path.join(PROJECT_ROOT, file_path)

    # 检查文件存在
    if not os.path.exists(full_path):
        return False, f"File not found: {file_path}"

    # 尝试 parse
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"
    except Exception as e:
        return False, f"Read error: {e}"

    return True, data


def validate_structure(data, rule):
    """验证数据结构：必需字段存在 + 类型正确"""
    errors = []

    # 检查必需字段存在
    for field in rule["required_fields"]:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # 检查字段类型
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
    print("TLL OS Canonical Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    for rule in VALIDATION_RULES:
        file_path = rule["path"]
        name = rule["name"]

        # 1. JSON parse
        parse_ok, parse_result = validate_json_file(file_path)

        if not parse_ok:
            print(f"❌ FAIL: {name}")
            print(f"   Error: {parse_result}")
            all_passed = False
            results.append((name, "FAIL", parse_result))
            continue

        data = parse_result

        # 2. 结构验证
        errors = validate_structure(data, rule)

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
        print("Canonical Validation PASS")
        print()
        print(f"Files:")
        for name, status, _ in results:
            print(f"  {name:30s} {status}")
        print()
        sys.exit(0)
    else:
        print("Canonical Validation FAIL")
        print()
        print(f"Files:")
        for name, status, err in results:
            if status == "PASS":
                print(f"  {name:30s} {status}")
            else:
                print(f"  {name:30s} {status} ({err})")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
