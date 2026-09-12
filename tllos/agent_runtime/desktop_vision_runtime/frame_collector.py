#!/usr/bin/env python3
"""
TLL OS Frame Collector

Multi-frame capture with hash chain.
Captures N consecutive frames, each with SHA256 hash.

Usage:
    python frame_collector.py [num_frames] [delay_ms]

Output:
    frame_sequence.json
    Multiple frame PNGs + metadata
"""

import sys
import os
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def compute_image_hash(image_path):
    """Compute SHA256 hash of image file."""
    h = hashlib.sha256()
    with open(image_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def capture_frame(frame_index, output_dir):
    """Capture a single frame and return metadata."""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        timestamp = datetime.now().isoformat()
        frame_id = f"seq-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{frame_index:03d}"
        frame_path = output_dir / f"{frame_id}.png"
        img.save(frame_path, format='PNG')
        frame_hash = compute_image_hash(str(frame_path))

        return {
            "frame_id": frame_id,
            "timestamp": timestamp,
            "hash": frame_hash,
            "width": img.width,
            "height": img.height,
            "source": "PIL_IMAGEGRAB",
            "file": str(frame_path.name)
        }
    except Exception as e:
        print(f"ERROR: Frame {frame_index} capture failed: {e}", file=sys.stderr)
        return None


def main():
    num_frames = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    delay_ms = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    print("=" * 60)
    print("TLL OS Frame Collector")
    print("=" * 60)
    print()
    print(f"Frames: {num_frames}")
    print(f"Delay: {delay_ms}ms")
    print()

    frames_dir = SCRIPT_DIR / "frames"
    frames_dir.mkdir(exist_ok=True)

    sequence_id = f"seq-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    frames = []

    for i in range(num_frames):
        print(f"Capturing frame {i+1}/{num_frames}...")
        frame = capture_frame(i, frames_dir)
        if frame:
            frames.append(frame)
            print(f"  ✅ {frame['frame_id']} ({frame['width']}x{frame['height']})")
            print(f"     Hash: {frame['hash'][:16]}...")
        else:
            print(f"  ❌ FAILED")
            sys.exit(1)

        if i < num_frames - 1:
            time.sleep(delay_ms / 1000.0)

    print()

    # Build sequence
    sequence = {
        "sequence_id": sequence_id,
        "created_at": datetime.now().isoformat(),
        "frame_count": len(frames),
        "frames": frames,
        "hash_chain": {
            "type": "sequential",
            "description": "Each frame captured at distinct timestamp, hash chained"
        },
        "schema_version": "1.0"
    }

    sequence_path = frames_dir / f"{sequence_id}.json"
    with open(sequence_path, 'w', encoding='utf-8') as f:
        json.dump(sequence, f, indent=2, ensure_ascii=False)

    print(f"Sequence saved: {sequence_path.name}")
    print(f"Total frames: {len(frames)}")
    print()

    # Show hash chain
    print("Hash Chain:")
    for i, frame in enumerate(frames):
        print(f"  Frame {i}: {frame['hash'][:16]}...")

    sys.exit(0)


if __name__ == "__main__":
    main()
