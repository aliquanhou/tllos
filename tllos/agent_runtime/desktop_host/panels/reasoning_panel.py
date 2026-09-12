#!/usr/bin/env python3
"""
TLL OS Desktop Host - Reasoning Panel
"""

import json
from pathlib import Path


class ReasoningPanel:
    def __init__(self, intelligence_dir):
        self.intel_dir = Path(intelligence_dir)

    def get_status(self):
        reasoning_file = self.intel_dir / "decisions" / "latest_reasoning.json"
        goal = ""
        decision = ""
        confidence = 0.0

        if reasoning_file.exists():
            with open(reasoning_file, 'r') as f:
                data = json.load(f)
            goal = data.get("goal", "")
            decision = data.get("decision", {}).get("action", "")
            confidence = data.get("confidence", 0.0)

        return {
            "goal": goal,
            "decision": decision,
            "confidence": confidence
        }

    def render(self):
        status = self.get_status()
        return f"🧠 REASONING\n  Goal: {status['goal']}\n  Decision: {status['decision']}\n  Confidence: {status['confidence']}"
