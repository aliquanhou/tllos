#!/usr/bin/env python3
"""
TLL OS Agent Operating Loop

Integrates Vision → Brain → Planner → Approval → Action → Verify → Reflect
"""

import sys
import json
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from agent_lifecycle import AgentLifecycle


class AgentOperatingLoop:
    def __init__(self, goal=""):
        self.goal = goal
        self.lifecycle = AgentLifecycle()
        self.session = {
            "session_id": self.lifecycle.session_id,
            "goal": goal,
            "steps": [],
            "events": [],
            "actions": [],
            "result": ""
        }

    def start(self):
        """Start agent loop."""
        self.lifecycle.add_event("LOOP_STARTED", {"goal": self.goal})
        self.lifecycle.transition("OBSERVING")
        self._add_event("LOOP_STARTED")

    def think(self):
        """Vision → Reasoning."""
        self.lifecycle.transition("THINKING")
        self._add_event("THINKING")

    def plan(self):
        """Generate plan."""
        self.lifecycle.transition("PLANNING")
        self.session["steps"] = ["OBSERVE", "ANALYZE", "EXECUTE", "VERIFY"]
        self._add_event("PLAN_CREATED", {"steps": self.session["steps"]})

    def request_approval(self):
        """Request human approval."""
        self.lifecycle.transition("WAIT_APPROVAL")
        self._add_event("APPROVAL_REQUIRED")

    def execute(self):
        """Execute action."""
        self.lifecycle.transition("EXECUTING")
        self.session["actions"].append({
            "type": "DEMO_ACTION",
            "timestamp": datetime.now().isoformat()
        })
        self._add_event("ACTION_STARTED")

    def verify(self):
        """Verify result."""
        self.lifecycle.transition("VERIFYING")
        self.session["result"] = "SUCCESS"
        self._add_event("VERIFICATION_DONE", {"result": "SUCCESS"})

    def reflect(self):
        """Reflect on execution."""
        self.lifecycle.transition("REFLECTING")
        self._add_event("REFLECTION_DONE", {"result": "success"})

    def complete(self):
        """Complete loop."""
        self.lifecycle.transition("COMPLETED")
        self._add_event("LOOP_COMPLETED")

    def emergency_stop(self):
        """Emergency stop."""
        self.lifecycle.state = "STOPPED"
        self._add_event("EMERGENCY_STOPPED")

    def _add_event(self, event_type, data=None):
        event = {
            "type": event_type,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        self.session["events"].append(event)

    def run_demo(self):
        """Run demo loop."""
        self.start()
        self.think()
        self.plan()
        self.request_approval()
        # Auto-approve for demo
        self.execute()
        self.verify()
        self.reflect()
        self.complete()
        return self.session

    def save_session(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.session, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    loop = AgentOperatingLoop(goal="Open Notepad and type Hello TLL")
    session = loop.run_demo()
    print("Session ID:", session["session_id"])
    print("Goal:", session["goal"])
    print("Steps:", session["steps"])
    print("Events:", len(session["events"]))
    print("Result:", session["result"])
