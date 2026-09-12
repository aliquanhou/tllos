#!/usr/bin/env python3
"""
TLL OS Vision Memory Runtime

Stores frame history, object history, confidence history.
Supports replay verification.

Usage:
    python vision_memory_runtime.py

Output:
    vision_memory.json
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_frames_from_history(frames_dir):
    """Load all frame metadata from frames directory."""
    frame_meta_files = sorted(Path(frames_dir).glob("*.json"), key=os.path.getmtime)
    frames = []

    for f in frame_meta_files:
        if f.name.startswith("seq-") or f.name.startswith("tracking"):
            continue
        try:
            with open(f, 'r') as fp:
                data = json.load(fp)
            frames.append({
                "frame_id": data.get("frame_id", f.stem),
                "hash": data.get("hash", data.get("frame_hash", "")),
                "timestamp": data.get("timestamp", ""),
                "type": "frame_metadata"
            })
        except:
            pass

    return frames


def load_objects_from_history(frames_dir):
    """Load object history."""
    obj_files = sorted(Path(frames_dir).glob("*.objects.json"), key=os.path.getmtime)
    objects = []

    for f in obj_files:
        try:
            with open(f, 'r') as fp:
                data = json.load(fp)
            objects.append({
                "frame_id": data.get("frame_id", ""),
                "frame_hash": data.get("frame_hash", ""),
                "total_objects": data.get("total_objects", 0),
                "detector": data.get("detector", "")
            })
        except:
            pass

    return objects


def verify_replay(frame_path, expected_hash):
    """Verify that replaying same frame gives same hash."""
    import hashlib
    h = hashlib.sha256()
    with open(frame_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    actual_hash = h.hexdigest()
    return actual_hash == expected_hash, actual_hash


def main():
    print("=" * 60)
    print("TLL OS Vision Memory Runtime")
    print("=" * 60)
    print()

    frames_dir = SCRIPT_DIR / "frames"
    frames_dir.mkdir(exist_ok=True)

    # Load history
    frames = load_frames_from_history(frames_dir)
    objects = load_objects_from_history(frames_dir)

    print(f"Frames in memory: {len(frames)}")
    print(f"Object records: {len(objects)}")
    print()

    # Replay verification
    print("Replay Verification:")
    replay_results = []
    for obj_record in objects[:3]:
        frame_id = obj_record["frame_id"]
        expected_hash = obj_record["frame_hash"]
        frame_path = frames_dir / f"{frame_id}.png"
        if frame_path.exists():
            match, actual_hash = verify_replay(str(frame_path), expected_hash)
            status = "✅ PASS" if match else "❌ FAIL"
            print(f"  {status} {frame_id}: hash match={match}")
            replay_results.append({
                "frame_id": frame_id,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "match": match
            })
        else:
            print(f"  ⚠️ SKIP {frame_id}: file not found")

    print()

    # Build memory
    memory = {
        "memory_id": f"mem-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "created_at": datetime.now().isoformat(),
        "frames": frames,
        "objects": objects,
        "replay_verification": replay_results,
        "memory_boundary": {
            "can_observe_history": True,
            "can_make_action_decision": False,
            "description": "Memory stores perception history only. No action decisions."
        },
        "schema_version": "1.0"
    }

    memory_path = SCRIPT_DIR / "vision_memory.json"
    with open(memory_path, 'w', encoding='utf-8') as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

    print(f"Memory saved: {memory_path.name}")
    print(f"Total frames: {len(frames)}")
    print(f"Total object records: {len(objects)}")
    print(f"Replay checks: {len(replay_results)}")

    sys.exit(0)


if __name__ == "__main__":
    main()
