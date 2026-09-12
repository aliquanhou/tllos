#!/usr/bin/env python3
"""
TLL OS Monitor Manager

Detects monitors and provides monitor info.
"""

import sys
import json
from pathlib import Path


def detect_monitors():
    """Detect available monitors using PySide6."""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        screens = app.screens()

        monitors = []
        for i, screen in enumerate(screens):
            geometry = screen.geometry()
            monitors.append({
                "id": i + 1,
                "name": screen.name(),
                "primary": (i == 0),
                "x": geometry.x(),
                "y": geometry.y(),
                "width": geometry.width(),
                "height": geometry.height()
            })

        return {
            "count": len(monitors),
            "monitors": monitors
        }
    except Exception as e:
        return {
            "count": 0,
            "monitors": [],
            "error": str(e)
        }


def get_monitor_info(monitor_id=2):
    """Get info for specific monitor."""
    result = detect_monitors()
    monitors = result.get("monitors", [])

    if monitor_id - 1 < len(monitors):
        return monitors[monitor_id - 1]

    # Fallback to primary
    return monitors[0] if monitors else None


if __name__ == "__main__":
    info = detect_monitors()
    print(json.dumps(info, indent=2))
