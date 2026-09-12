#!/usr/bin/env python3
"""
TLL OS Object Tracking Validator

Gates:
- Gate 1: Tracking Schema
- Gate 2: Track Evidence
- Gate 3: Movement Calculation
- Gate 4: Identity Binding
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
    print("TLL OS Object Tracking Validation")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    # Gate 1: Tracking Schema
    print("--- Gate 1: Tracking Schema ---")
    ok, schema = validate_json_file("tllos/agent_runtime/desktop_vision_runtime/object_tracking.json")
    if not ok:
        print(f"  >> FAIL: {schema}")
        all_passed = False
        results.append(("Gate 1: Tracking Schema", "FAIL"))
    else:
        required = ["track_id", "current_position", "movement", "confidence", "schema_version"]
        missing = [f for f in required if f not in schema]
        if missing:
            print(f"  >> FAIL: missing: {missing}")
            all_passed = False
            results.append(("Gate 1: Tracking Schema", "FAIL"))
        else:
            print(f"  >> PASS: tracking schema valid")
            results.append(("Gate 1: Tracking Schema", "PASS"))

    # Gate 2: Track Evidence
    print()
    print("--- Gate 2: Track Evidence ---")
    frames_dir = os.path.join(PROJECT_ROOT, "tllos/agent_runtime/desktop_vision_runtime/frames")
    tracking_path = os.path.join(frames_dir, "tracking.json")
    if not os.path.exists(tracking_path):
        print(f"  >> FAIL: tracking.json not found")
        all_passed = False
        results.append(("Gate 2: Track Evidence", "FAIL"))
    else:
        with open(tracking_path, 'r') as f:
            tracking = json.load(f)
        track_count = tracking.get("total_tracks", 0)
        print(f"  Total tracks: {track_count}")
        if track_count > 0:
            print(f"  >> PASS: tracking evidence present")
            results.append(("Gate 2: Track Evidence", "PASS"))
        else:
            print(f"  >> FAIL: no tracks")
            all_passed = False
            results.append(("Gate 2: Track Evidence", "FAIL"))

    # Gate 3: Movement Calculation
    print()
    print("--- Gate 3: Movement Calculation ---")
    if 'tracking' in dir() and tracking.get("tracks"):
        first_track = tracking["tracks"][0]
        movement = first_track.get("movement", {})
        required_movement = ["dx", "dy", "distance"]
        missing = [m for m in required_movement if m not in movement]
        if missing:
            print(f"  >> FAIL: missing movement fields: {missing}")
            all_passed = False
            results.append(("Gate 3: Movement Calculation", "FAIL"))
        else:
            print(f"  Movement: dx={movement['dx']:.1f}, dy={movement['dy']:.1f}, dist={movement['distance']:.1f}")
            print(f"  >> PASS: movement calculation present")
            results.append(("Gate 3: Movement Calculation", "PASS"))
    else:
        print(f"  >> FAIL: no tracks to verify")
        all_passed = False
        results.append(("Gate 3: Movement Calculation", "FAIL"))

    # Gate 4: Identity Binding
    print()
    print("--- Gate 4: Identity Binding ---")
    if 'tracking' in dir() and tracking.get("tracks"):
        first_track = tracking["tracks"][0]
        if "track_id" in first_track and "object_type" in first_track:
            print(f"  Track ID: {first_track['track_id']}")
            print(f"  Type: {first_track['object_type']}")
            print(f"  >> PASS: identity bound")
            results.append(("Gate 4: Identity Binding", "PASS"))
        else:
            print(f"  >> FAIL: identity fields missing")
            all_passed = False
            results.append(("Gate 4: Identity Binding", "FAIL"))
    else:
        print(f"  >> FAIL: no tracks")
        all_passed = False
        results.append(("Gate 4: Identity Binding", "FAIL"))

    print()
    print("=" * 60)
    if all_passed:
        print("Object Tracking Validation PASS")
        print(f"  4/4 Gates Verified")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        sys.exit(0)
    else:
        print("Object Tracking Validation FAIL")
        print()
        for name, status in results:
            print(f"  {name:40s} {status}")
        sys.exit(1)


if __name__ == "__main__":
    main()
