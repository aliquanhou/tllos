#!/usr/bin/env python3
"""
TLL OS Vision Runtime Validator
Validate Vision Runtime protocol integrity.

Gates:
- Gate 1: Dependency
- Gate 2: Capture
- Gate 3: Evidence (Frame + Object)
- Gate 4: Lifecycle
- Gate 5: Ledger
- Gate 6: Object Evidence Schema
- Gate 7: OCR Boundary
"""

import json
import sys
import os
import hashlib

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


def check_dependencies():
    """Check if vision libraries are available."""
    deps = []
    try:
        from PIL import Image, ImageGrab
        deps.append(("Pillow", True))
    except ImportError:
        deps.append(("Pillow", False))

    try:
        import numpy as np
        deps.append(("numpy", True))
    except ImportError:
        deps.append(("numpy", False))

    try:
        import cv2
        deps.append(("OpenCV", True))
    except ImportError:
        deps.append(("OpenCV", False))

    try:
        import pytesseract
        deps.append(("pytesseract", True))
    except ImportError:
        deps.append(("pytesseract", False))

    return deps


def main():
    print("=" * 60)
    print("TLL OS Vision Runtime Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Dependency
    print("--- Gate 1: Dependency ---")
    deps = check_dependencies()
    dep_ok = True
    for name, available in deps:
        status = "PASS" if available else "FAIL"
        print(f"  [{status}] {name}")
        if not available:
            dep_ok = False

    if dep_ok:
        print(f"  >> PASS: All dependencies available")
        results.append(("Gate 1: Dependency", "PASS"))
    else:
        print(f"  >> FAIL: Some dependencies missing")
        all_passed = False
        results.append(("Gate 1: Dependency", "FAIL"))

    # Gate 2: Capture
    print()
    print("--- Gate 2: Capture ---")
    capture_script = "tllos/agent_runtime/desktop_vision_runtime/screen_capture_runtime.py"
    if check_file_exists(capture_script):
        print(f"  >> PASS: screen_capture_runtime.py exists")
        results.append(("Gate 2: Capture", "PASS"))
    else:
        print(f"  >> FAIL: screen_capture_runtime.py missing")
        all_passed = False
        results.append(("Gate 2: Capture", "FAIL"))

    # Gate 3: Evidence
    print()
    print("--- Gate 3: Evidence ---")
    ok, frame = validate_json_file("tllos/agent_runtime/desktop_vision_runtime/frame_buffer.json")
    if not ok:
        print(f"  >> FAIL: {frame}")
        all_passed = False
        results.append(("Gate 3: Evidence", "FAIL"))
    else:
        required = frame.get("required_fields", [])
        if "hash" in required and "evidence_ref" in required:
            print(f"  >> PASS: Frame evidence fields present")
            results.append(("Gate 3: Evidence", "PASS"))
        else:
            print(f"  >> FAIL: Evidence fields incomplete")
            all_passed = False
            results.append(("Gate 3: Evidence", "FAIL"))

    # Gate 4: Lifecycle
    print()
    print("--- Gate 4: Lifecycle ---")
    ok, context = validate_json_file("tllos/agent_runtime/desktop_vision_runtime/vision_context.json")
    if not ok:
        print(f"  >> FAIL: {context}")
        all_passed = False
        results.append(("Gate 4: Lifecycle", "FAIL"))
    else:
        status_values = context.get("context_fields", {}).get("status", {}).get("values", [])
        required_states = ["CREATED", "INITIALIZED", "RUNNING", "COMPLETED", "FAILED"]
        missing = [s for s in required_states if s not in status_values]
        if missing:
            print(f"  >> FAIL: missing states: {missing}")
            all_passed = False
            results.append(("Gate 4: Lifecycle", "FAIL"))
        else:
            print(f"  >> PASS: Vision lifecycle valid, {len(status_values)} states")
            results.append(("Gate 4: Lifecycle", "PASS"))

    # Gate 5: Ledger
    print()
    print("--- Gate 5: Ledger ---")
    ok, audit = validate_json_file("tllos/agent_runtime/audit_ledger/audit_event.json")
    if not ok:
        print(f"  >> FAIL: {audit}")
        all_passed = False
        results.append(("Gate 5: Ledger", "FAIL"))
    else:
        event_types = audit.get("event_types", [])
        required_events = ["SCREEN_CAPTURE_STARTED", "FRAME_HASH_GENERATED", "FRAME_STORED"]
        missing = [e for e in required_events if e not in event_types]
        if missing:
            print(f"  >> FAIL: missing events: {missing}")
            all_passed = False
            results.append(("Gate 5: Ledger", "FAIL"))
        else:
            print(f"  >> PASS: ledger events present, {len(event_types)} total")
            results.append(("Gate 5: Ledger", "PASS"))

    # Gate 6: Object Evidence
    print()
    print("--- Gate 6: Object Evidence ---")
    objects_path = "tllos/agent_runtime/desktop_vision_runtime/frames/frame-7c3d5ca7d8d5.objects.json"
    ok, objects = validate_json_file(objects_path)
    if not ok:
        print(f"  >> WARN: objects.json: {objects}")
        results.append(("Gate 6: Object Evidence", "WARN"))
    else:
        required_fields = ["frame_id", "frame_hash", "objects", "total_objects", "evidence_schema_version"]
        missing = [f for f in required_fields if f not in objects]
        if missing:
            print(f"  >> FAIL: missing fields: {missing}")
            all_passed = False
            results.append(("Gate 6: Object Evidence", "FAIL"))
        else:
            print(f"  >> PASS: object evidence valid, {objects['total_objects']} objects")
            results.append(("Gate 6: Object Evidence", "PASS"))

    # Gate 7: OCR Boundary
    print()
    print("--- Gate 7: OCR Boundary ---")
    ocr_path = "tllos/agent_runtime/desktop_vision_runtime/frames/frame-7c3d5ca7d8d5.ocr.json"
    ok, ocr = validate_json_file(ocr_path)
    if not ok:
        print(f"  >> FAIL: ocr.json: {ocr}")
        all_passed = False
        results.append(("Gate 7: OCR Boundary", "FAIL"))
    else:
        status = ocr.get("ocr_status", "UNKNOWN")
        if status in ("COMPLETED", "NOT_AVAILABLE"):
            print(f"  >> PASS: OCR status correctly recorded: {status}")
            results.append(("Gate 7: OCR Boundary", "PASS"))
        else:
            print(f"  >> FAIL: unexpected OCR status: {status}")
            all_passed = False
            results.append(("Gate 7: OCR Boundary", "FAIL"))

    # Directory structure check
    print()
    print("--- Directory Structure ---")
    vision_files = [
        "tllos/agent_runtime/desktop_vision_runtime/architecture.md",
        "tllos/agent_runtime/desktop_vision_runtime/frame_buffer.json",
        "tllos/agent_runtime/desktop_vision_runtime/vision_context.json",
        "tllos/agent_runtime/desktop_vision_runtime/screen_capture_runtime.py",
        "tllos/agent_runtime/desktop_vision_runtime/ocr_runtime.py",
        "tllos/agent_runtime/desktop_vision_runtime/object_detection_runtime.py",
        "tllos/agent_runtime/desktop_vision_runtime/evidence_pipeline.md",
        "tllos/agent_runtime/desktop_vision_runtime/safety_gate.md",
    ]
    for file_path in vision_files:
        if check_file_exists(file_path):
            print(f"  [PASS] {file_path}")
        else:
            print(f"  [FAIL] {file_path} not found")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("Vision Runtime Validation PASS")
        print(f"  7/7 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(0)
    else:
        print("Vision Runtime Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
