#!/usr/bin/env python3
"""
TLL OS Object Detection Runtime

鍩轰簬瑙勫垯鐨勭洰鏍囨娴?v1銆?浣跨敤 OpenCV 杩涜绠€鍗曠殑鐭╁舰/杈圭紭妫€娴嬨€?
鐢ㄦ硶锛?    python object_detection_runtime.py [image_path]

杈撳嚭锛?    Vision Objects (JSON)
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


def detect_objects_rule_based(image_path):
    """
    鍩轰簬瑙勫垯鐨勭洰鏍囨娴?v1銆?    妫€娴嬬煩褰㈣疆寤撲綔涓?UI 鎺т欢銆?
    杩斿洖 Vision Objects (list of dict)銆?    """
    try:
        import cv2
        import numpy as np

        # 璇诲彇鍥惧儚
        img = cv2.imread(image_path)
        if img is None:
            print(f"ERROR: Cannot read image: {image_path}", file=sys.stderr)
            return []

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 杈圭紭妫€娴?        edges = cv2.Canny(gray, 50, 150)

        # 鏌ユ壘杞粨
        contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        objects = []
        frame_id = Path(image_path).stem

        for i, contour in enumerate(contours):
            # 璁＄畻闈㈢Н
            area = cv2.contourArea(contour)

            # 杩囨护灏忓尯鍩?            if area < 100 or area > 1000000:
                continue

            # 杩戜技澶氳竟褰?            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # 鑾峰彇杈圭晫妗?            x, y, w, h = cv2.boundingRect(approx)

            # 鍒ゆ柇绫诲瀷锛堢畝鍗曡鍒欙級
            aspect_ratio = w / h if h > 0 else 1
            fill_ratio = area / (w * h) if w * h > 0 else 0

            if aspect_ratio < 0.3:
                obj_type = "CONTROL"  # 缁嗛暱鎺т欢
            elif aspect_ratio > 3:
                obj_type = "TEXT"     # 闀挎潯褰㈡枃鏈尯鍩?            elif 0.8 < aspect_ratio < 1.2:
                obj_type = "ICON"     # 杩戜技姝ｆ柟褰?            else:
                obj_type = "PANEL"    # 涓€鑸潰鏉?
            obj = {
                "object_id": f"obj-{frame_id}-{i:04d}",
                "type": obj_type,
                "position": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h)
                },
                "confidence": 0.7,  # 瑙勫垯妫€娴嬬殑缃俊搴?                "area": float(area),
                "aspect_ratio": float(aspect_ratio),
                "evidence_ref": f"ev-{frame_id}-{i:04d}",
                "audit_ref": f"audit-{frame_id}-{i:04d}"
            }
            objects.append(obj)

        return objects

    except Exception as e:
        print(f"ERROR: Object detection failed: {e}", file=sys.stderr)
        return []


def main():
    """涓诲叆鍙ｃ€?""
    print("=" * 60)
    print("TLL OS Object Detection Runtime")
    print("=" * 60)
    print()

    # 榛樿浣跨敤鏈€鏂扮殑鎴浘
    frames_dir = SCRIPT_DIR / "frames"
    if not frames_dir.exists():
        print("鉂?FAIL: No frames directory found")
        sys.exit(1)

    # 鎵炬渶鏂扮殑 PNG
    png_files = sorted(frames_dir.glob("*.png"), key=os.path.getmtime, reverse=True)
    if not png_files:
        print("鉂?FAIL: No PNG frames found")
        sys.exit(1)

    latest_frame = png_files[0]
    print(f"Processing: {latest_frame.name}")
    print()

    # Object Detection
    objects = detect_objects_rule_based(str(latest_frame))

    print(f"鉁?Object Detection SUCCESS: {len(objects)} objects found")
    print()

    # 杈撳嚭鍓?10 涓?    for i, obj in enumerate(objects[:10]):
        print(f"  [{i+1}] {obj['type']:10s} at ({obj['position']['x']:4d}, {obj['position']['y']:4d}) "
              f"{obj['position']['width']:4d}x{obj['position']['height']:4d} (conf: {obj['confidence']:.2f})")

    if len(objects) > 10:
        print(f"  ... and {len(objects) - 10} more")

    print()

    # 淇濆瓨缁撴灉
    result_path = latest_frame.with_suffix('.objects.json')
    result = {
        "frame_id": latest_frame.stem,
        "timestamp": datetime.now().isoformat(),
        "detector": "rule_based_v1",
        "objects": objects,
        "total_objects": len(objects)
    }

    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Result saved: {result_path}")

    sys.exit(0)


if __name__ == "__main__":
    main()
