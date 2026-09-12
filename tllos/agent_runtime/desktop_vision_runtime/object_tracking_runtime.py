#!/usr/bin/env python3
"""
TLL OS Object Tracking Runtime

Basic object tracking across frames.
Uses centroid distance matching.

Usage:
    python object_tracking_runtime.py [frame_json1] [frame_json2]

Output:
    tracking.json
"""

import sys
import os
import json
import math
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_centroid(bbox):
    """Get centroid from bounding box."""
    cx = bbox['x'] + bbox['width'] / 2
    cy = bbox['y'] + bbox['height'] / 2
    return (cx, cy)


def distance(p1, p2):
    """Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def match_objects(prev_objects, curr_objects, max_distance=100):
    """Match objects between frames using centroid distance."""
    matches = []
    used_prev = set()

    for curr_obj in curr_objects:
        curr_centroid = get_centroid(curr_obj['bbox'])
        best_dist = float('inf')
        best_prev = None

        for i, prev_obj in enumerate(prev_objects):
            if i in used_prev:
                continue
            prev_centroid = get_centroid(prev_obj['bbox'])
            dist = distance(prev_centroid, curr_centroid)
            if dist < best_dist and dist < max_distance:
                best_dist = dist
                best_prev = (i, prev_obj)

        if best_prev:
            prev_idx, prev_obj = best_prev
            used_prev.add(prev_idx)

            prev_cx, prev_cy = get_centroid(prev_obj['bbox'])
            curr_cx, curr_cy = get_centroid(curr_obj['bbox'])

            track = {
                "track_id": prev_obj.get("object_id", "unknown"),
                "object_type": curr_obj["type"],
                "previous_position": prev_obj["bbox"],
                "current_position": curr_obj["bbox"],
                "centroid": {"x": curr_cx, "y": curr_cy},
                "movement": {
                    "dx": curr_cx - prev_cx,
                    "dy": curr_cy - prev_cy,
                    "distance": best_dist
                },
                "confidence": curr_obj["confidence"],
                "first_seen": prev_obj.get("evidence_ref", ""),
                "last_seen": curr_obj.get("evidence_ref", ""),
                "schema_version": "1.0"
            }
            matches.append(track)

    return matches


def main():
    print("=" * 60)
    print("TLL OS Object Tracking Runtime")
    print("=" * 60)
    print()

    frames_dir = SCRIPT_DIR / "frames"

    # Get objects from two frames
    obj_files = sorted(frames_dir.glob("*.objects.json"), key=os.path.getmtime, reverse=True)
    if len(obj_files) < 2:
        print("WARN: Need at least 2 object files for tracking")
        print("Using single frame demo...")
        if len(obj_files) == 1:
            with open(obj_files[0], 'r') as f:
                data = json.load(f)
            objects = data.get("objects", [])
            print(f"Objects: {len(objects)}")
            # Create self-tracking demo
            tracks = []
            for obj in objects[:10]:
                tracks.append({
                    "track_id": obj["object_id"],
                    "object_type": obj["type"],
                    "previous_position": obj["bbox"],
                    "current_position": obj["bbox"],
                    "movement": {"dx": 0, "dy": 0, "distance": 0},
                    "confidence": obj["confidence"],
                    "frame_hash": data.get("frame_hash", ""),
                    "schema_version": "1.0"
                })
        else:
            print("ERROR: No object files found")
            sys.exit(1)
    else:
        # Load two latest frames
        with open(obj_files[0], 'r') as f:
            curr_data = json.load(f)
        with open(obj_files[1], 'r') as f:
            prev_data = json.load(f)

        prev_objects = prev_data.get("objects", [])
        curr_objects = curr_data.get("objects", [])

        print(f"Previous frame: {len(prev_objects)} objects")
        print(f"Current frame: {len(curr_objects)} objects")
        print()

        tracks = match_objects(prev_objects, curr_objects)
        print(f"Tracked: {len(tracks)} objects")

    print()
    print("Top tracked objects:")
    for i, track in enumerate(tracks[:5]):
        print(f"  [{i+1}] {track['track_id']:30s} "
              f"type={track['object_type']:8s} "
              f"dist={track['movement']['distance']:.1f}px")

    # Save tracking evidence
    result = {
        "tracking_id": f"track-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "tracks": tracks,
        "total_tracks": len(tracks),
        "tracking_method": "centroid_distance_v1",
        "schema_version": "1.0"
    }

    output_path = frames_dir / "tracking.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print()
    print(f"Tracking evidence saved: {output_path.name}")

    sys.exit(0)


if __name__ == "__main__":
    main()
