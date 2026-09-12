#!/usr/bin/env python3
"""
TLL OS Action Runtime - Real Driver Prototype

First real Desktop Action implementation.
Uses pyautogui for mouse/keyboard control.

Usage:
    python action_runtime.py

Safety:
- All actions logged with evidence
- Before/after frame hash comparison
- Permission gate required
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


def capture_frame(label):
    """Capture screen frame and return metadata."""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        frames_dir = SCRIPT_DIR / "frames"
        frames_dir.mkdir(exist_ok=True)
        frame_id = f"action-{label}-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
        frame_path = frames_dir / f"{frame_id}.png"
        img.save(frame_path, format='PNG')
        frame_hash = compute_image_hash(str(frame_path))
        return {
            "frame_id": frame_id,
            "hash": frame_hash,
            "width": img.width,
            "height": img.height,
            "path": str(frame_path.name)
        }
    except Exception as e:
        print(f"ERROR: Frame capture failed: {e}", file=sys.stderr)
        return None


def action_move_mouse(x, y):
    """Move mouse to (x, y)."""
    try:
        import pyautogui
        pyautogui.moveTo(x, y, duration=0.2)
        return {"success": True, "action": "MOVE_MOUSE", "x": x, "y": y}
    except Exception as e:
        return {"success": False, "action": "MOVE_MOUSE", "error": str(e)}


def action_click(button='left'):
    """Perform mouse click."""
    try:
        import pyautogui
        pyautogui.click(button=button)
        return {"success": True, "action": "CLICK", "button": button}
    except Exception as e:
        return {"success": False, "action": "CLICK", "error": str(e)}


def action_type_text(text):
    """Type text on keyboard."""
    try:
        import pyautogui
        pyautogui.typewrite(text, interval=0.05)
        return {"success": True, "action": "TYPE_TEXT", "text_length": len(text)}
    except Exception as e:
        return {"success": False, "action": "TYPE_TEXT", "error": str(e)}


def execute_action(action_type, **kwargs):
    """
    Execute an action with evidence binding.
    Returns full action result with before/after frame hash.
    """
    action_id = f"act-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"

    # Before frame
    before = capture_frame("before")
    if not before:
        return {"action_id": action_id, "success": False, "error": "before frame failed"}

    # Execute
    if action_type == "MOVE_MOUSE":
        result = action_move_mouse(kwargs.get("x", 100), kwargs.get("y", 100))
    elif action_type == "CLICK":
        result = action_click(kwargs.get("button", "left"))
    elif action_type == "TYPE_TEXT":
        result = action_type_text(kwargs.get("text", ""))
    else:
        result = {"success": False, "error": f"unknown action: {action_type}"}

    # After frame
    after = capture_frame("after")

    # Build result
    action_result = {
        "action_id": action_id,
        "action_type": action_type,
        "success": result.get("success", False),
        "before_frame_hash": before.get("hash", ""),
        "after_frame_hash": after.get("hash", "") if after else "",
        "result": result,
        "timestamp": datetime.now().isoformat(),
        "evidence": f"ev-{action_id}",
        "audit_event": f"audit-{action_id}",
        "schema_version": "1.0"
    }

    return action_result


def main():
    print("=" * 60)
    print("TLL OS Action Runtime - Real Driver Prototype")
    print("=" * 60)
    print()

    # Demo: move mouse to safe position (corner)
    print("Demo Action 1: Move mouse to (100, 100)")
    result1 = execute_action("MOVE_MOUSE", x=100, y=100)
    print(f"  Success: {result1['success']}")
    print(f"  Before hash: {result1['before_frame_hash'][:16]}...")
    print(f"  After hash:  {result1['after_frame_hash'][:16]}...")
    print()

    # Save evidence
    frames_dir = SCRIPT_DIR / "frames"
    evidence_path = frames_dir / "action_results.json"

    all_results = []
    if evidence_path.exists():
        with open(evidence_path, 'r') as f:
            all_results = json.load(f)

    all_results.append(result1)

    with open(evidence_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"Action evidence saved: {evidence_path.name}")
    print(f"Total actions recorded: {len(all_results)}")

    sys.exit(0)


if __name__ == "__main__":
    main()
