#!/usr/bin/env python3
"""
TLL OS Desktop Host - Action Panel
"""

import json
from pathlib import Path


class ActionPanel:
    def __init__(self, action_dir):
        self.action_dir = Path(action_dir)

    def get_status(self):
        results_file = self.action_dir / "frames" / "action_results.json"
        current = ""
        result = ""
        before_hash = ""
        after_hash = ""

        if results_file.exists():
            with open(results_file, 'r') as f:
                actions = json.load(f)
            if actions:
                last = actions[-1]
                current = last.get("action_type", "")
                result = "SUCCESS" if last.get("success") else "FAILED"
                before_hash = last.get("before_frame_hash", "")[:16]
                after_hash = last.get("after_frame_hash", "")[:16]

        return {
            "current": current,
            "result": result,
            "before_hash": before_hash,
            "after_hash": after_hash
        }

    def render(self):
        status = self.get_status()
        return (f"🖱 ACTION\n"
                f"  Last: {status['current']}\n"
                f"  Result: {status['result']}\n"
                f"  Before: {status['before_hash']}\n"
                f"  After:  {status['after_hash']}")
