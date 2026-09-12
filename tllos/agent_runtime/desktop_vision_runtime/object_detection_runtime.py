#!/usr/bin/env python3
"""
TLL OS Object Detection Runtime

Rule-based object detection v1.
Uses OpenCV for rectangle/edge detection.

Usage:
    python object_detection_runtime.py [image_path]

Output:
    Vision Objects (JSON)
"""

import sys
import os
import json
import hashlib
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


def detect_objects_rule_based(image_path):
    """
    Rule-based object detection v1.
    Detects rectangle contours as UI controls.
    Returns Vision Objects (list of dict).
    """
    try:
        import cv2
        import numpy as np

        img = cv2.imread(image_path)
        if img is None:
            print(f"ERROR: Cannot read image: {image_path}", file=sys.stderr)
            return []

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        objects = []
        frame_id = Path(image_path).stem

        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area < 100 or area > 1000000:
                continue

            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            x, y, w, h = cv2.boundingRect(approx)

            aspect_ratio = w / h if h > 0 else 1
            fill_ratio = area / (w * h) if w * h > 0 else 0

            if aspect_ratio < 0.3:
                obj_type = "CONTROL"
            elif aspect_ratio > 3:
                obj_type = "TEXT"
            elif 0.8 < aspect_ratio < 1.2:
                obj_type = "ICON"
            else:
                obj_type = "PANEL"

            obj = {
                "object_id": f"obj-{frame_id}-{i:04d}",
                "type": obj_type,
                "bbox": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h)
                },
                "confidence": 0.7,
                "area": float(area),
                "aspect_ratio": float(aspect_ratio),
                "source_frame": frame_id,
                "evidence_ref": f"ev-{frame_id}-{i:04d}",
                "audit_ref": f"audit-{frame_id}-{i:04d}"
            }
            objects.append(obj)

        return objects

    except Exception as e:
        print(f"ERROR: Object detection failed: {e}", file=sys.stderr)
        return []


def write_evidence(objects, frame_path, output_path):
    """Write detection results to evidence JSON file."""
    frame_hash = compute_image_hash(frame_path)
    frame_id = Path(frame_path).stem

    result = {
        "frame_id": frame_id,
        "frame_hash": frame_hash,
        "timestamp": datetime.now().isoformat(),
        "detector": "rule_based_v1",
        "objects": objects,
        "total_objects": len(objects),
        "evidence_schema_version": "1.0"
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def main():
    print("=" * 60)
    print("TLL OS Object Detection Runtime")
    print("=" * 60)
    print()

    frames_dir = SCRIPT_DIR / "frames"
    if not frames_dir.exists():
        print("FAIL: No frames directory found")
        sys.exit(1)

    png_files = sorted(frames_dir.glob("*.png"), key=os.path.getmtime, reverse=True)
    if not png_files:
        print("FAIL: No PNG frames found")
        sys.exit(1)

    latest_frame = png_files[0]
    print(f"Processing: {latest_frame.name}")
    print()

    objects = detect_objects_rule_based(str(latest_frame))
    print(f"SUCCESS: {len(objects)} objects found")
    print()

    for i, obj in enumerate(objects[:10]):
        bbox = obj['bbox']
        print(f"  [{i+1}] {obj['type']:10s} at ({bbox['x']:4d}, {bbox['y']:4d}) "
              f"{bbox['width']:4d}x{bbox['height']:4d} (conf: {obj['confidence']:.2f})")

    if len(objects) > 10:
        print(f"  ... and {len(objects) - 10} more")
    print()

    result_path = latest_frame.with_suffix('.objects.json')
    result = write_evidence(objects, str(latest_frame), str(result_path))
    print(f"Evidence saved: {result_path.name}")
    print(f"Frame hash: {result['frame_hash'][:16]}...")

    sys.exit(0)


if __name__ == "__main__":
    main()
