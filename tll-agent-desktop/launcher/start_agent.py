#!/usr/bin/env python3
"""
TLL OS Desktop Agent Launcher

Starts the TLL Desktop Agent Cockpit on the second monitor.
"""

import sys
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent.parent
COCKPIT_DIR = REPO_ROOT / "tllos" / "agent_runtime" / "desktop_cockpit"
CONFIG_DIR = SCRIPT_DIR.parent / "config"

sys.path.insert(0, str(COCKPIT_DIR))


def load_config():
    config_file = CONFIG_DIR / "monitor.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}


def detect_monitors():
    """Detect available monitors."""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        screens = app.screens()
        print(f"Detected {len(screens)} monitor(s):")
        for i, screen in enumerate(screens):
            print(f"  Monitor {i+1}: {screen.name()}")
        return screens
    except Exception as e:
        print(f"Monitor detection: {e}")
        return []


def main():
    print("=" * 60)
    print("TLL OS Desktop Agent Launcher")
    print("=" * 60)
    print()

    config = load_config()
    print(f"Config: {config.get('monitor', {}).get('target_monitor', 'default')}")

    print()
    screens = detect_monitors()

    if len(screens) >= 2:
        target = config.get('monitor', {}).get('target_monitor', 2) - 1
        print(f"\nLaunching Cockpit on Monitor {target+1}...")
        # Launch cockpit
        from main_window import main as cockpit_main
        cockpit_main()
    elif len(screens) == 1:
        print("\nSingle monitor detected. Launching on primary screen.")
        from main_window import main as cockpit_main
        cockpit_main()
    else:
        print("\nNo screens detected. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
