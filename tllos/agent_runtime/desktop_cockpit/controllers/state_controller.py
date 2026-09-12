#!/usr/bin/env python3
"""
TLL OS Desktop Cockpit - State Controller

Reads agent state from JSON files.
"""

import json
from pathlib import Path
from datetime import datetime


class StateController:
    def __init__(self, project_root):
        self.root = Path(project_root)
        self.vision_dir = self.root / "tllos" / "agent_runtime" / "desktop_vision_runtime"
        self.intel_dir = self.root / "tllos" / "agent_runtime" / "intelligence"
        self.planner_dir = self.root / "tllos" / "agent_runtime" / "action_planner"
        self.action_dir = self.root / "tllos" / "agent_runtime" / "desktop_action_runtime"

    def get_vision_state(self):
        frames_dir = self.vision_dir / "frames"
        if not frames_dir.exists():
            return {"frame": "", "objects": 0, "hash": ""}
        frame_files = sorted(frames_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not frame_files:
            return {"frame": "", "objects": 0, "hash": ""}
        with open(frame_files[0], 'r') as f:
            data = json.load(f)
        objects_file = frames_dir / "objects.json"
        objects_count = 0
        if objects_file.exists():
            with open(objects_file, 'r') as f:
                obj_data = json.load(f)
            objects_count = obj_data.get("total_objects", len(obj_data.get("objects", [])))
        return {
            "frame": data.get("frame_id", frame_files[0].stem),
            "objects": objects_count,
            "hash": data.get("hash", data.get("frame_hash", ""))[:16]
        }

    def get_reasoning_state(self):
        reasoning_file = self.intel_dir / "decisions" / "latest_reasoning.json"
        if not reasoning_file.exists():
            return {"goal": "", "decision": "", "confidence": 0.0}
        with open(reasoning_file, 'r') as f:
            data = json.load(f)
        return {
            "goal": data.get("goal", ""),
            "decision": data.get("decision", {}).get("action", ""),
            "confidence": data.get("confidence", 0.0)
        }

    def get_plan_state(self):
        plan_file = self.planner_dir / "plans" / "latest_plan.json"
        if not plan_file.exists():
            return {"steps": [], "current_step": 0}
        with open(plan_file, 'r') as f:
            data = json.load(f)
        steps = [s.get("action_type", s.get("action", "")) for s in data.get("steps", [])]
        return {"steps": steps, "current_step": data.get("current_step", 0)}

    def get_action_state(self):
        results_file = self.action_dir / "frames" / "action_results.json"
        if not results_file.exists():
            return {"current": "", "result": "", "before_hash": "", "after_hash": ""}
        with open(results_file, 'r') as f:
            actions = json.load(f)
        if not actions:
            return {"current": "", "result": "", "before_hash": "", "after_hash": ""}
        last = actions[-1]
        return {
            "current": last.get("action_type", ""),
            "result": "SUCCESS" if last.get("success") else "FAILED",
            "before_hash": last.get("before_frame_hash", "")[:16],
            "after_hash": last.get("after_frame_hash", "")[:16]
        }

    def get_full_state(self):
        return {
            "vision": self.get_vision_state(),
            "reasoning": self.get_reasoning_state(),
            "plan": self.get_plan_state(),
            "action": self.get_action_state(),
            "timestamp": datetime.now().isoformat()
        }
