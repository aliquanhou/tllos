#!/usr/bin/env python3
"""
TLL OS Desktop Host - Event Bus

Simple pub/sub for agent state updates.
"""

import json
from datetime import datetime
from pathlib import Path


class EventBus:
    def __init__(self):
        self.subscribers = {}
        self.events = []

    def subscribe(self, event_type, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type, data):
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.events.append(event)
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)

    def get_recent_events(self, count=10):
        return self.events[-count:]

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.events[-100:], f, indent=2, ensure_ascii=False)
