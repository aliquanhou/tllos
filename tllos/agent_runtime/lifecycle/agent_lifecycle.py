#!/usr/bin/env python3
"""
TLL OS Agent Lifecycle

State machine for autonomous agent operation.
"""

import json
from datetime import datetime
from pathlib import Path


# Valid state transitions
VALID_TRANSITIONS = {
    "CREATED": ["OBSERVING"],
    "OBSERVING": ["THINKING", "FAILED", "STOPPED"],
    "THINKING": ["PLANNING", "FAILED", "STOPPED"],
    "PLANNING": ["WAIT_APPROVAL", "FAILED", "STOPPED"],
    "WAIT_APPROVAL": ["EXECUTING", "DENIED", "STOPPED"],
    "EXECUTING": ["VERIFYING", "FAILED", "STOPPED"],
    "VERIFYING": ["REFLECTING", "FAILED", "STOPPED"],
    "REFLECTING": ["COMPLETED", "OBSERVING", "FAILED", "STOPPED"],
    "COMPLETED": ["CREATED"],
    "FAILED": ["OBSERVING", "STOPPED"],
    "DENIED": ["PLANNING", "STOPPED"],
    "PAUSED": ["OBSERVING", "STOPPED"],
    "STOPPED": []
}


class AgentLifecycle:
    def __init__(self, session_id=""):
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.state = "CREATED"
        self.previous_state = ""
        self.timestamp = datetime.now().isoformat()
        self.history = []
        self.events = []

    def transition(self, new_state):
        """Transition to new state if valid."""
        if new_state not in VALID_TRANSITIONS.get(self.state, []):
            raise ValueError(f"Invalid transition: {self.state} -> {new_state}")
        self.previous_state = self.state
        self.state = new_state
        self.timestamp = datetime.now().isoformat()
        self.history.append({
            "from": self.previous_state,
            "to": self.state,
            "timestamp": self.timestamp
        })
        return self.get_state()

    def get_state(self):
        return {
            "session_id": self.session_id,
            "state": self.state,
            "previous_state": self.previous_state,
            "timestamp": self.timestamp
        }

    def add_event(self, event_type, data=None):
        event = {
            "type": event_type,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "state": self.state
        }
        self.events.append(event)
        return event

    def save(self, path):
        data = {
            "session_id": self.session_id,
            "state": self.state,
            "previous_state": self.previous_state,
            "timestamp": self.timestamp,
            "history": self.history,
            "events": self.events
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def is_valid_transition(self, from_state, to_state):
        return to_state in VALID_TRANSITIONS.get(from_state, [])


# Demo
if __name__ == "__main__":
    lifecycle = AgentLifecycle()
    print("Initial:", lifecycle.get_state())
    lifecycle.transition("OBSERVING")
    print("After observing:", lifecycle.get_state())
    lifecycle.transition("THINKING")
    print("After thinking:", lifecycle.get_state())
    lifecycle.transition("PLANNING")
    print("After planning:", lifecycle.get_state())
    lifecycle.transition("WAIT_APPROVAL")
    print("After wait approval:", lifecycle.get_state())
    lifecycle.transition("EXECUTING")
    print("After executing:", lifecycle.get_state())
    lifecycle.transition("VERIFYING")
    print("After verifying:", lifecycle.get_state())
    lifecycle.transition("REFLECTING")
    print("After reflecting:", lifecycle.get_state())
    lifecycle.transition("COMPLETED")
    print("After completed:", lifecycle.get_state())
    print()
    print(f"Total transitions: {len(lifecycle.history)}")
