#!/usr/bin/env python3
"""
TLL OS OCR Runtime

鐪熷疄 OCR 瀹炵幇锛屼娇鐢?pytesseract銆?
鐢ㄦ硶锛?    python ocr_runtime.py [image_path]

杈撳嚭锛?    Text Regions (JSON)
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


def ocr_image(image_path):
    """
    瀵瑰浘鍍忔墽琛?OCR銆?
    杩斿洖 Text Regions (list of dict)銆?    """
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)

        # 鑾峰彇璇︾粏鏁版嵁
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        regions = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if text and int(data['conf'][i]) > 30:  # confidence > 30%
                region = {
                    "text": text,
                    "confidence": float(data['conf'][i]) / 100.0,
                    "position": {
                        "x": int(data['left'][i]),
                        "y": int(data['top'][i]),
                        "width": int(data['width'][i]),
                        "height": int(data['height'][i])
                    },
                    "block_num": int(data['block_num'][i]),
                    "line_num": int(data['line_num'][i])
                }
                regions.append(region)

        return regions

    except Exception as e:
        print(f"ERROR: OCR failed: {e}", file=sys.stderr)
        return []


def main():
    """涓诲叆鍙ｃ€?""
    print("=" * 60)
    print("TLL OS OCR Runtime")
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

    # OCR
    regions = ocr_image(str(latest_frame))

    print(f"鉁?OCR SUCCESS: {len(regions)} text regions found")
    print()

    # 杈撳嚭鍓?10 涓?    for i, r in enumerate(regions[:10]):
        print(f"  [{i+1}] \"{r['text']}\" (conf: {r['confidence']:.2f}) at ({r['position']['x']}, {r['position']['y']})")

    if len(regions) > 10:
        print(f"  ... and {len(regions) - 10} more")

    print()

    # 淇濆瓨缁撴灉
    result_path = latest_frame.with_suffix('.ocr.json')
    result = {
        "frame_id": latest_frame.stem,
        "timestamp": datetime.now().isoformat(),
        "ocr_engine": "pytesseract",
        "text_regions": regions,
        "total_regions": len(regions)
    }

    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Result saved: {result_path}")

    sys.exit(0)


if __name__ == "__main__":
    main()
