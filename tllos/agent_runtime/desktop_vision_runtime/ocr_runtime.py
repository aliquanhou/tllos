#!/usr/bin/env python3
"""
TLL OS OCR Runtime

OCR wrapper using pytesseract.
Boundary: If Tesseract engine is not installed, returns NOT_AVAILABLE.
No fake OCR claims.

Usage:
    python ocr_runtime.py [image_path]

Output:
    Text Objects (JSON) or NOT_AVAILABLE
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


def check_tesseract_available():
    """Check if Tesseract engine is available on system."""
    try:
        import pytesseract
        # Try to get tesseract version
        version = pytesseract.get_tesseract_version()
        return True, str(version)
    except Exception as e:
        return False, str(e)


def compute_image_hash(image_path):
    """Compute SHA256 hash of image file."""
    h = hashlib.sha256()
    with open(image_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def run_ocr(image_path):
    """
    Run OCR on image.
    Returns list of text objects.
    """
    available, info = check_tesseract_available()
    if not available:
        return {
            "status": "NOT_AVAILABLE",
            "reason": f"Tesseract engine not available: {info}"
        }

    try:
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        text_objects = []
        frame_id = Path(image_path).stem

        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = int(data['conf'][i]) if data['conf'][i] != -1 else 0

            if text and conf > 0:
                obj = {
                    "object_id": f"ocr-{frame_id}-{i:04d}",
                    "type": "TEXT",
                    "text": text,
                    "bbox": {
                        "x": int(data['left'][i]),
                        "y": int(data['top'][i]),
                        "width": int(data['width'][i]),
                        "height": int(data['height'][i])
                    },
                    "confidence": conf / 100.0,
                    "source_frame": frame_id,
                    "evidence_ref": f"ev-ocr-{frame_id}-{i:04d}"
                }
                text_objects.append(obj)

        return {
            "status": "COMPLETED",
            "objects": text_objects,
            "total_objects": len(text_objects)
        }

    except Exception as e:
        return {
            "status": "FAILED",
            "reason": str(e)
        }


def write_ocr_evidence(ocr_result, frame_path, output_path):
    """Write OCR results to evidence JSON file."""
    frame_hash = compute_image_hash(frame_path)
    frame_id = Path(frame_path).stem

    result = {
        "frame_id": frame_id,
        "frame_hash": frame_hash,
        "timestamp": datetime.now().isoformat(),
        "ocr_status": ocr_result.get("status", "UNKNOWN"),
        "evidence_schema_version": "1.0"
    }

    if ocr_result.get("status") == "COMPLETED":
        result["objects"] = ocr_result.get("objects", [])
        result["total_objects"] = ocr_result.get("total_objects", 0)
    else:
        result["reason"] = ocr_result.get("reason", "Unknown")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def main():
    print("=" * 60)
    print("TLL OS OCR Runtime")
    print("=" * 60)
    print()

    available, info = check_tesseract_available()
    print(f"Tesseract available: {available}")
    if available:
        print(f"Version: {info}")
    else:
        print(f"Reason: {info}")
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

    ocr_result = run_ocr(str(latest_frame))
    print(f"OCR Status: {ocr_result['status']}")

    if ocr_result['status'] == "COMPLETED":
        print(f"Text objects: {ocr_result['total_objects']}")

    result_path = latest_frame.with_suffix('.ocr.json')
    result = write_ocr_evidence(ocr_result, str(latest_frame), str(result_path))
    print(f"Evidence saved: {result_path.name}")

    sys.exit(0 if ocr_result['status'] in ("COMPLETED", "NOT_AVAILABLE") else 1)


if __name__ == "__main__":
    main()
