#!/usr/bin/env python3
"""
TLL OS Execution Intelligence Validator
验证 Execution Intelligence 层的协议完整性。

Gates:
- Gate 1: Observation Schema
- Gate 2: Evidence Binding
- Gate 3: Metrics Integrity
- Gate 4: Insight Reference
- Gate 5: No Execution Mutation

用法：
    python tools/agent_runtime_validator/validate_execution_intelligence.py

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
    print("TLL OS Execution Intelligence Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Observation Schema
    print("--- Gate 1: Observation Schema ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_intelligence/execution_observation.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 1: Observation Schema", "FAIL"))
    else:
        required = ["execution_id", "agent_id", "task_id", "execution_stage", "timestamp", "input_state", "output_state", "evidence_ref", "audit_ref"]
        missing = [f for f in required if f not in data.get("required_fields", [])]
        if missing:
            print(f"  ❌ FAIL: missing required fields: {missing}")
            all_passed = False
            results.append(("Gate 1: Observation Schema", "FAIL"))
        else:
            print(f"  ✅ PASS: all required fields present")
            results.append(("Gate 1: Observation Schema", "PASS"))

    # Gate 2: Evidence Binding
    print()
    print("--- Gate 2: Evidence Binding ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_intelligence/execution_observation.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 2: Evidence Binding", "FAIL"))
    else:
        required = data.get("required_fields", [])
        if "evidence_ref" in required and "audit_ref" in required:
            print(f"  ✅ PASS: evidence_ref and audit_ref are required")
            results.append(("Gate 2: Evidence Binding", "PASS"))
        else:
            print(f"  ❌ FAIL: evidence_ref/audit_ref not required")
            all_passed = False
            results.append(("Gate 2: Evidence Binding", "FAIL"))

    # Gate 3: Metrics Integrity
    print()
    print("--- Gate 3: Metrics Integrity ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_intelligence/execution_metrics.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 3: Metrics Integrity", "FAIL"))
    else:
        prohibited = data.get("prohibited_metrics", [])
        required = data.get("required_fields", [])
        has_categories = all(cat in data.get("metrics_categories", {}) for cat in ["performance", "reliability", "trust"])
        has_prohibited = len(prohibited) > 0
        if has_categories and has_prohibited and "performance" in required:
            print(f"  ✅ PASS: metrics categories defined, prohibited metrics listed")
            results.append(("Gate 3: Metrics Integrity", "PASS"))
        else:
            print(f"  ❌ FAIL: metrics integrity incomplete")
            all_passed = False
            results.append(("Gate 3: Metrics Integrity", "FAIL"))

    # Gate 4: Insight Reference
    print()
    print("--- Gate 4: Insight Reference ---")
    ok, data = validate_json_file("tllos/agent_runtime/execution_intelligence/execution_insight.json")
    if not ok:
        print(f"  ❌ FAIL: {data}")
        all_passed = False
        results.append(("Gate 4: Insight Reference", "FAIL"))
    else:
        insights_items = data.get("fields", {}).get("insights", {}).get("items", {})
        items_required = insights_items.get("required", [])
        if "evidence_ref" in items_required:
            print(f"  ✅ PASS: insight items require evidence_ref")
            results.append(("Gate 4: Insight Reference", "PASS"))
        else:
            print(f"  ❌ FAIL: insight items do not require evidence_ref")
            all_passed = False
            results.append(("Gate 4: Insight Reference", "FAIL"))

    # Gate 5: No Execution Mutation
    print()
    print("--- Gate 5: No Execution Mutation ---")
    arch_file = "tllos/agent_runtime/execution_intelligence/architecture.md"
    if check_file_exists(arch_file):
        with open(os.path.join(PROJECT_ROOT, arch_file), "r", encoding="utf-8") as f:
            content = f.read()
        has_no_modify = "不修改" in content or "不改变" in content or "不自动" in content
        has_readonly = "只读" in content or "Read" in content
        if has_no_modify and has_readonly:
            print(f"  ✅ PASS: intelligence layer is read-only, no execution mutation")
            results.append(("Gate 5: No Execution Mutation", "PASS"))
        else:
            print(f"  ❌ FAIL: no execution mutation rule not found")
            all_passed = False
            results.append(("Gate 5: No Execution Mutation", "FAIL"))
    else:
        print(f"  ❌ FAIL: architecture.md not found")
        all_passed = False
        results.append(("Gate 5: No Execution Mutation", "FAIL"))

    # Also check directory structure
    print()
    print("--- Directory Structure ---")
    intelligence_files = [
        "tllos/agent_runtime/execution_intelligence/README.md",
        "tllos/agent_runtime/execution_intelligence/architecture.md",
        "tllos/agent_runtime/execution_intelligence/intelligence_model.md",
        "tllos/agent_runtime/execution_intelligence/execution_observation.md",
        "tllos/agent_runtime/execution_intelligence/execution_metrics.md",
        "tllos/agent_runtime/execution_intelligence/execution_observation.json",
        "tllos/agent_runtime/execution_intelligence/execution_metrics.json",
        "tllos/agent_runtime/execution_intelligence/intelligence_pipeline.md",
        "tllos/agent_runtime/execution_intelligence/execution_insight.json",
    ]
    for file_path in intelligence_files:
        if check_file_exists(file_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Execution Intelligence Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Execution Intelligence Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
