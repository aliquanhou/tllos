#!/usr/bin/env python3
"""
TLL OS Desktop Host - Vision Panel

Reads vision runtime state and formats for display.
"""

import json
from pathlib import Path


class VisionPanel:
    def __init__(self, vision_runtime_dir):
        self.vision_dir = Path(vision_runtime_dir)

    def get_status(self):
        frames_dir = self.vision_dir / "frames"
        objects_count = 0
        latest_frame = ""
        latest_hash = ""

        if frames_dir.exists():
            frame_files = sorted(frames_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
            if frame_files:
                with open(frame_files[0], 'r') as f:
                    data = json.load(f)
                latest_frame = data.get("frame_id", frame_files[0].stem)
                latest_hash = data.get("hash", data.get("frame_hash", ""))[:16]

            objects_file = frames_dir / "objects.json"
            if objects_file.exists():
                with open(objects_file, 'r') as f:
                    obj_data = json.load(f)
                objects_count = obj_data.get("total_objects", len(obj_data.get("objects", [])))

        return {
            "frame": latest_frame,
            "hash": latest_hash,
            "objects": objects_count
        }

    def render(self):
        status = self.get_status()
        return f"👁 VISION\n  Frame: {status['frame']}\n  Hash:  {status['hash']}\n  Objects: {status['objects']}"
