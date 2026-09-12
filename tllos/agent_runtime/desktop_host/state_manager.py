#!/usr/bin/env python3
"""
TLL OS Desktop Host - State Manager

Manages unified agent state.
"""

import json
from datetime import datetime
from pathlib import Path


class StateManager:
    def __init__(self):
        self.state = {
            "agent_id": "tll-agent-001",
            "state": "IDLE",
            "vision": {
                "frame": "",
                "objects": 0,
                "hash": ""
            },
            "reasoning": {
                "goal": "",
                "decision": "",
                "confidence": 0.0
            },
            "plan": {
                "steps": [],
                "current_step": 0
            },
            "action": {
                "current": "",
                "result": "",
                "before_hash": "",
                "after_hash": ""
            },
            "evidence": {
                "hash": "",
                "timestamp": ""
            },
            "updated_at": ""
        }

    def update(self, section, data):
        if section in self.state:
            self.state[section].update(data)
            self.state["updated_at"] = datetime.now().isoformat()

    def set_state(self, state):
        self.state["state"] = state
        self.state["updated_at"] = datetime.now().isoformat()

    def get_state(self):
        return self.state.copy()

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def load(self, path):
        if Path(path).exists():
            with open(path, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
