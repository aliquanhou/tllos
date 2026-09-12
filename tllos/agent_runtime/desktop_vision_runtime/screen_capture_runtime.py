#!/usr/bin/env python3
"""
TLL OS Screen Capture Runtime

鐪熷疄灞忓箷閲囬泦瀹炵幇锛圵indows锛夈€?浣跨敤 PIL.ImageGrab 瀹炵幇鐪熷疄鎴浘銆?
鐢ㄦ硶锛?    python screen_capture_runtime.py [--fullscreen | --region X Y W H]

杈撳嚭锛?    PNG 鏂囦欢 + Frame Metadata (JSON)
"""

import sys
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

# 娣诲姞椤圭洰鏍圭洰褰曞埌 path
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def capture_fullscreen():
    """鍏ㄥ睆鎴浘銆?""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        return img
    except Exception as e:
        print(f"ERROR: Failed to capture fullscreen: {e}", file=sys.stderr)
        return None


def capture_region(region):
    """鍖哄煙鎴浘銆俽egion = (x, y, width, height)"""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(bbox=region)
        return img
    except Exception as e:
        print(f"ERROR: Failed to capture region: {e}", file=sys.stderr)
        return None


def compute_hash(img):
    """璁＄畻鍥惧儚鐨?SHA256 Hash銆?""
    import io
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return hashlib.sha256(buf.getvalue()).hexdigest()


def generate_frame_id():
    """鐢熸垚鍞竴 Frame ID銆?""
    from uuid import uuid4
    return f"frame-{uuid4().hex[:12]}"


def capture_and_save(output_dir="tllos/agent_runtime/desktop_vision_runtime/frames"):
    """
    鎵ц鎴浘骞朵繚瀛樸€?
    杩斿洖 Frame Metadata (dict)銆?    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Capture
    img = capture_fullscreen()
    if img is None:
        return None

    # 2. Generate metadata
    frame_id = generate_frame_id()
    timestamp = datetime.now().isoformat()
    width, height = img.size
    hash_val = compute_hash(img)

    # 3. Save
    filename = f"{frame_id}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath, 'PNG')

    # 4. Frame metadata
    metadata = {
        "frame_id": frame_id,
        "timestamp": timestamp,
        "width": width,
        "height": height,
        "format": "PNG",
        "source": "PIL_IMAGECRAP",
        "hash": hash_val,
        "file_path": filepath,
        "evidence_ref": f"ev-{frame_id}",
        "audit_ref": f"audit-{frame_id}"
    }

    # 5. Save metadata
    meta_path = os.path.join(output_dir, f"{frame_id}.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return metadata


def main():
    """涓诲叆鍙ｃ€?""
    print("=" * 60)
    print("TLL OS Screen Capture Runtime")
    print("=" * 60)
    print()

    # 鎵ц鎴浘
    metadata = capture_and_save()

    if metadata is None:
        print("鉂?FAIL: Screen capture failed")
        sys.exit(1)

    # 杈撳嚭缁撴灉
    print("鉁?Screen Capture SUCCESS")
    print()
    print(f"  Frame ID:    {metadata['frame_id']}")
    print(f"  Resolution:  {metadata['width']}x{metadata['height']}")
    print(f"  Format:      {metadata['format']}")
    print(f"  Source:      {metadata['source']}")
    print(f"  Hash:        {metadata['hash'][:16]}...")
    print(f"  File:        {metadata['file_path']}")
    print()

    sys.exit(0)


if __name__ == "__main__":
    main()
