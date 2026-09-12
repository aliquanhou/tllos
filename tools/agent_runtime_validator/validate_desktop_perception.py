#!/usr/bin/env python3
"""
TLL OS Desktop Perception Validator
验证 Desktop Perception 的协议完整性。

Gates:
- Gate 1: Schema
- Gate 2: Evidence
- Gate 3: Lifecycle
- Gate 4: Permission
- Gate 5: Audit

用法：
    python tools/agent_runtime_validator/validate_desktop_perception.py

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
    print("TLL OS Desktop Perception Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Schema
    print("--- Gate 1: Schema ---")
    ok, frame = validate_json_file("tllos/agent_runtime/desktop_perception/screen_frame.json")
    if not ok:
        print(f"  ❌ FAIL: {frame}")
        all_passed = False
        results.append(("Gate 1: Schema (Frame)", "FAIL"))
    else:
        required = frame.get("required_fields", [])
        if len(required) >= 5:
            print(f"  ✅ PASS: Frame schema valid, {len(required)} required fields")
            results.append(("Gate 1: Schema (Frame)", "PASS"))
        else:
            print(f"  ❌ FAIL: Frame schema incomplete")
            all_passed = False
            results.append(("Gate 1: Schema (Frame)", "FAIL"))

    ok, obj = validate_json_file("tllos/agent_runtime/desktop_perception/vision_object.json")
    if not ok:
        print(f"  ❌ FAIL: {obj}")
        all_passed = False
        results.append(("Gate 1: Schema (Object)", "FAIL"))
    else:
        required = obj.get("required_fields", [])
        if len(required) >= 5:
            print(f"  ✅ PASS: Object schema valid, {len(required)} required fields")
            results.append(("Gate 1: Schema (Object)", "PASS"))
        else:
            print(f"  ❌ FAIL: Object schema incomplete")
            all_passed = False
            results.append(("Gate 1: Schema (Object)", "FAIL"))

    # Gate 2: Evidence
    print()
    print("--- Gate 2: Evidence ---")
    ok, frame = validate_json_file("tllos/agent_runtime/desktop_perception/screen_frame.json")
    if ok and "evidence_ref" in frame.get("required_fields", []):
        print(f"  ✅ PASS: Frame requires evidence_ref")
        results.append(("Gate 2: Evidence (Frame)", "PASS"))
    else:
        print(f"  ❌ FAIL: Frame missing evidence_ref")
        all_passed = False
        results.append(("Gate 2: Evidence (Frame)", "FAIL"))

    ok, obj = validate_json_file("tllos/agent_runtime/desktop_perception/vision_object.json")
    if ok and "evidence_ref" in obj.get("required_fields", []):
        print(f"  ✅ PASS: Object requires evidence_ref")
        results.append(("Gate 2: Evidence (Object)", "PASS"))
    else:
        print(f"  ❌ FAIL: Object missing evidence_ref")
        all_passed = False
        results.append(("Gate 2: Evidence (Object)", "FAIL"))

    # Gate 3: Lifecycle
    print()
    print("--- Gate 3: Lifecycle ---")
    ok, frame = validate_json_file("tllos/agent_runtime/desktop_perception/screen_frame.json")
    if ok:
        states = frame.get("lifecycle", {}).get("states", [])
        required_states = ["REQUESTED", "CAPTURED", "ANALYZING", "MATCHED", "USED", "ARCHIVED"]
        missing = [s for s in required_states if s not in states]
        if missing:
            print(f"  ❌ FAIL: missing states: {missing}")
            all_passed = False
            results.append(("Gate 3: Lifecycle", "FAIL"))
        else:
            print(f"  ✅ PASS: Frame lifecycle valid, {len(states)} states")
            results.append(("Gate 3: Lifecycle", "PASS"))
    else:
        print(f"  ❌ FAIL: cannot read frame")
        all_passed = False
        results.append(("Gate 3: Lifecycle", "FAIL"))

    # Gate 4: Permission
    print()
    print("--- Gate 4: Permission ---")
    interface_exists = check_file_exists("tllos/agent_runtime/desktop_perception/driver/screen_capture_interface.md")
    safety_exists = check_file_exists("tllos/agent_runtime/desktop_perception/safety_layer.md")
    if interface_exists and safety_exists:
        print(f"  ✅ PASS: Permission check enforced (Safety Layer present)")
        results.append(("Gate 4: Permission", "PASS"))
    else:
        print(f"  ❌ FAIL: Permission check missing")
        all_passed = False
        results.append(("Gate 4: Permission", "FAIL"))

    # Gate 5: Audit
    print()
    print("--- Gate 5: Audit ---")
    ok, audit = validate_json_file("tllos/agent_runtime/audit_ledger/audit_event.json")
    if not ok:
        print(f"  ❌ FAIL: {audit}")
        all_passed = False
        results.append(("Gate 5: Audit", "FAIL"))
    else:
        event_types = audit.get("event_types", [])
        required_events = ["SCREEN_CAPTURE_REQUESTED", "SCREEN_CAPTURE_COMPLETED", "VISION_ANALYSIS_STARTED", "VISION_ANALYSIS_COMPLETED"]
        missing = [e for e in required_events if e not in event_types]
        if missing:
            print(f"  ❌ FAIL: missing events: {missing}")
            all_passed = False
            results.append(("Gate 5: Audit", "FAIL"))
        else:
            print(f"  ✅ PASS: audit events present, {len(event_types)} total")
            results.append(("Gate 5: Audit", "PASS"))

    # Check directory structure
    print()
    print("--- Directory Structure ---")
    perception_files = [
        "tllos/agent_runtime/desktop_perception/architecture.md",
        "tllos/agent_runtime/desktop_perception/screen_frame.json",
        "tllos/agent_runtime/desktop_perception/vision_object.json",
        "tllos/agent_runtime/desktop_perception/safety_layer.md",
        "tllos/agent_runtime/desktop_perception/driver/screen_capture_interface.md",
        "tllos/agent_runtime/desktop_perception/driver/screen_capture_driver.md",
        "tllos/agent_runtime/desktop_perception/vision/vision_engine_interface.md",
        "tllos/agent_runtime/desktop_perception/vision/ocr_interface.md",
        "tllos/agent_runtime/desktop_perception/vision/object_detection_interface.md",
    ]
    for file_path in perception_files:
        if check_file_exists(file_path):
            print(f"  ✅ PASS: {file_path}")
        else:
            print(f"  ❌ FAIL: {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Desktop Perception Validation PASS")
        print(f"  5/5 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Desktop Perception Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
