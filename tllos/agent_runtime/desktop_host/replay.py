#!/usr/bin/env python3
"""
TLL OS Desktop Host - Replay

Replays past agent behavior from audit events.
"""

import json
from pathlib import Path


class AgentReplay:
    def __init__(self, audit_ledger_path):
        self.ledger_path = Path(audit_ledger_path)

    def load_events(self, count=20):
        if not self.ledger_path.exists():
            return []
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        events = data.get("events", data) if isinstance(data, dict) else data
        return events[-count:]

    def replay(self, count=10):
        events = self.load_events(count)
        print("=" * 60)
        print("TLL AGENT REPLAY")
        print("=" * 60)
        print()
        for i, event in enumerate(events):
            event_type = event.get("event_type", event.get("type", "UNKNOWN"))
            timestamp = event.get("timestamp", "")
            print(f"  {i+1}. [{timestamp}] {event_type}")
        print()
        print(f"Total events replayed: {len(events)}")
        return events
