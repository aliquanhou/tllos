#!/usr/bin/env python3
"""
TLL OS Desktop Host - Runtime

Main host entry point.
"""

import sys
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from event_bus import EventBus
from state_manager import StateManager


class DesktopHost:
    def __init__(self):
        self.event_bus = EventBus()
        self.state_manager = StateManager()
        self.running = False

    def start(self):
        self.running = True
        self.state_manager.set_state("RUNNING")
        self.event_bus.publish("HOST_STARTED", {"status": "running"})
        print("TLL Desktop Agent Host started")

    def stop(self):
        self.running = False
        self.state_manager.set_state("STOPPED")
        self.event_bus.publish("HOST_STOPPED", {"status": "stopped"})
        print("TLL Desktop Agent Host stopped")

    def pause(self):
        self.state_manager.set_state("PAUSED")
        self.event_bus.publish("HOST_PAUSED", {"status": "paused"})

    def wait_approval(self):
        self.state_manager.set_state("WAIT_APPROVAL")
        self.event_bus.publish("HOST_WAIT_APPROVAL", {"status": "waiting_approval"})

    def resume(self):
        self.state_manager.set_state("RUNNING")
        self.event_bus.publish("HOST_RESUMED", {"status": "running"})

    # Safety: Console must NOT directly call pyautogui.
    # All actions go through Permission Gate -> Action Runtime.

    def get_snapshot(self):
        return self.state_manager.get_state()

    def save_snapshot(self, path):
        self.state_manager.save(path)


def main():
    print("=" * 60)
    print("TLL OS Desktop Agent Host")
    print("=" * 60)
    print()

    host = DesktopHost()
    host.start()

    # Demo: update state
    host.state_manager.update("vision", {"frame": "frame-7c3d5ca7", "objects": 104})
    host.state_manager.update("reasoning", {"goal": "Open calculator", "confidence": 0.85})
    host.state_manager.update("action", {"current": "MOVE_MOUSE", "result": "SUCCESS"})

    # Save snapshot
    snapshots_dir = SCRIPT_DIR / "snapshots"
    snapshots_dir.mkdir(exist_ok=True)
    host.save_snapshot(snapshots_dir / "latest_snapshot.json")

    print()
    print("Snapshot saved: snapshots/latest_snapshot.json")
    print(f"State: {host.get_snapshot()['state']}")
    print(f"Vision objects: {host.get_snapshot()['vision']['objects']}")
    print(f"Reasoning goal: {host.get_snapshot()['reasoning']['goal']}")

    host.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()
