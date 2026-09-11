#!/usr/bin/env python3
"""
TLL OS Trust Chain Validator
验证 Trust Chain 的完整性和一致性。

不依赖外部库，使用内置 json 模块进行基本结构验证。

用法：
    python tools/agent_runtime_validator/validate_trust_chain.py

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


def validate_trust_verification_file(data):
    errors = []
    required = ["verification_name", "verification_version", "required_chain_elements", "validation_rules"]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    elements = data.get("required_chain_elements", {})
    for layer in ["identity", "capability", "permission", "execution", "evidence", "audit_ledger"]:
        if layer not in elements:
            errors.append(f"Missing chain element: {layer}")

    return errors


def validate_verification_rules_file(data):
    errors = []
    required = ["rules_name", "rules_version", "rules", "status_transitions"]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    rules = data.get("rules", [])
    if len(rules) < 5:
        errors.append(f"Expected at least 5 rules, got {len(rules)}")

    return errors


def main():
    print("=" * 60)
    print("TLL OS Trust Chain Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Case 1: trust_verification.json
    print("--- Case 1: trust_verification.json ---")
    parse_ok, result = validate_json_file("tllos/agent_runtime/trust/trust_verification.json")
    if not parse_ok:
        print(f"❌ FAIL: {result}")
        all_passed = False
        results.append(("trust_verification.json", "FAIL", result))
    else:
        errors = validate_trust_verification_file(result)
        if errors:
            print(f"❌ FAIL")
            for err in errors:
                print(f"   - {err}")
            all_passed = False
            results.append(("trust_verification.json", "FAIL", "; ".join(errors)))
        else:
            print(f"✅ PASS")
            results.append(("trust_verification.json", "PASS", ""))

    # Case 2: verification_rules.json
    print()
    print("--- Case 2: verification_rules.json ---")
    parse_ok, result = validate_json_file("tllos/agent_runtime/trust/verification_rules.json")
    if not parse_ok:
        print(f"❌ FAIL: {result}")
        all_passed = False
        results.append(("verification_rules.json", "FAIL", result))
    else:
        errors = validate_verification_rules_file(result)
        if errors:
            print(f"❌ FAIL")
            for err in errors:
                print(f"   - {err}")
            all_passed = False
            results.append(("verification_rules.json", "FAIL", "; ".join(errors)))
        else:
            print(f"✅ PASS")
            results.append(("verification_rules.json", "PASS", ""))

    # Case 3: trust_chain.md exists
    print()
    print("--- Case 3: trust_chain.md ---")
    trust_md = os.path.join(PROJECT_ROOT, "tllos/agent_runtime/trust/trust_chain.md")
    if os.path.exists(trust_md):
        print(f"✅ PASS: file exists")
        results.append(("trust_chain.md", "PASS", ""))
    else:
        print(f"❌ FAIL: file not found")
        all_passed = False
        results.append(("trust_chain.md", "FAIL", "file not found"))

    # Case 4: README.md exists
    print()
    print("--- Case 4: README.md ---")
    readme_md = os.path.join(PROJECT_ROOT, "tllos/agent_runtime/trust/README.md")
    if os.path.exists(readme_md):
        print(f"✅ PASS: file exists")
        results.append(("README.md", "PASS", ""))
    else:
        print(f"❌ FAIL: file not found")
        all_passed = False
        results.append(("README.md", "FAIL", "file not found"))

    print()
    print("=" * 60)
    if all_passed:
        print("Trust Chain Validation PASS")
        print()
        for name, status, _ in results:
            print(f"  {name:30s} {status}")
        print()
        sys.exit(0)
    else:
        print("Trust Chain Validation FAIL")
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
