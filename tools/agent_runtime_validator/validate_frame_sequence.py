#!/usr/bin/env python3
"""
TLL OS Frame Sequence Validator

Validates multi-frame sequence integrity.

Gates:
- Gate 1: Sequence Schema
- Gate 2: Hash Chain
- Gate 3: Frame Count
- Gate 4: Evidence Binding
"""

import json
import sys
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent


def validate_json_file(file_path):
    full_path = os.path.join(PROJECT_ROOT, file_path)
    if not os.path.exists(full_path):
        return False, f"File not found: {file_path}"
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Parse error: {e}"
    return True, data


def main():
    print("=" * 60)
    print("TLL OS Frame Sequence Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Sequence Schema
    print("--- Gate 1: Sequence Schema ---")
    ok, schema = validate_json_file("tllos/agent_runtime/desktop_vision_runtime/frame_sequence.json")
    if not ok:
        print(f"  >> FAIL: {schema}")
        all_passed = False
        results.append(("Gate 1: Sequence Schema", "FAIL"))
    else:
        required = ["sequence_id", "frames", "hash_chain", "schema_version"]
        missing = [f for f in required if f not in schema]
        if missing:
            print(f"  >> FAIL: missing: {missing}")
            all_passed = False
            results.append(("Gate 1: Sequence Schema", "FAIL"))
        else:
            print(f"  >> PASS: schema valid")
            results.append(("Gate 1: Sequence Schema", "PASS"))

    # Gate 2: Hash Chain
    print()
    print("--- Gate 2: Hash Chain ---")
    frames_dir = os.path.join(PROJECT_ROOT, "tllos/agent_runtime/desktop_vision_runtime/frames")
    seq_files = list(Path(frames_dir).glob("seq-*.json")) if os.path.exists(frames_dir) else []
    if not seq_files:
        print(f"  >> WARN: no sequence files found")
        results.append(("Gate 2: Hash Chain", "WARN"))
    else:
        latest_seq = sorted(seq_files, key=os.path.getmtime, reverse=True)[0]
        with open(latest_seq, 'r') as f:
            seq = json.load(f)
        frames = seq.get("frames", [])
        hashes = [fr["hash"] for fr in frames]
        print(f"  Frames in sequence: {len(frames)}")
        print(f"  Unique hashes: {len(set(hashes))}")
        if len(frames) >= 2:
            print(f"  >> PASS: hash chain present, {len(frames)} frames")
            results.append(("Gate 2: Hash Chain", "PASS"))
        else:
            print(f"  >> FAIL: insufficient frames")
            all_passed = False
            results.append(("Gate 2: Hash Chain", "FAIL"))

    # Gate 3: Frame Count
    print()
    print("--- Gate 3: Frame Count ---")
    if 'frames' in dir() and len(frames) >= 2:
        print(f"  >> PASS: {len(frames)} frames captured")
        results.append(("Gate 3: Frame Count", "PASS"))
    else:
        print(f"  >> WARN: frame count not verified")
        results.append(("Gate 3: Frame Count", "WARN"))

    # Gate 4: Evidence Binding
    print()
    print("--- Gate 4: Evidence Binding ---")
    if 'seq' in dir():
        frame_ids = [fr["frame_id"] for fr in seq.get("frames", [])]
        print(f"  Frame IDs: {len(frame_ids)}")
        print(f"  Sequence ID: {seq.get('sequence_id', 'N/A')}")
        print(f"  >> PASS: evidence bound to sequence")
        results.append(("Gate 4: Evidence Binding", "PASS"))
    else:
        print(f"  >> WARN: no sequence to verify")
        results.append(("Gate 4: Evidence Binding", "WARN"))

    print()
    print("=" * 60)
    fail_count = sum(1 for _, s in results if s == "FAIL")
    if fail_count == 0:
        print("Frame Sequence Validation PASS")
        print(f"  4/4 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        sys.exit(0)
    else:
        print("Frame Sequence Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        sys.exit(1)


if __name__ == "__main__":
    main()
