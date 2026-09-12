#!/usr/bin/env python3
"""
TLL OS App Runtime

Real application lifecycle management for TLL OS.
"""

import time
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class VirtualApp:
    """Virtual application."""
    app_id: str
    name: str
    type: str = "window"  # window / console / service
    status: str = "CREATED"  # CREATED / LAUNCHED / RUNNING / CLOSED
    window_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    launched_at: Optional[float] = None


class TLLAppRuntime:
    """TLL OS App Runtime - application lifecycle management."""

    def __init__(self, window_manager=None, process_manager=None):
        self.wm = window_manager
        self.process_mgr = process_manager
        self.apps: Dict[str, VirtualApp] = {}

    def create_app(self, name: str, type: str = "window") -> Dict:
        """Create a new application."""
        app_id = f"app-{uuid.uuid4().hex[:8]}"

        app = VirtualApp(
            app_id=app_id,
            name=name,
            type=type
        )
        self.apps[app_id] = app

        return {
            "app_id": app_id,
            "name": name,
            "type": type,
            "status": app.status
        }

    def launch_app(self, app_id: str) -> Dict:
        """Launch an application."""
        if app_id not in self.apps:
            return {"app_id": app_id, "error": "App not found"}

        app = self.apps[app_id]
        app.status = "LAUNCHED"
        app.launched_at = time.time()

        # Create window if it's a window app
        if app.type == "window" and self.wm:
            win = self.wm.create_window(
                title=app.name,
                x=100 + len(self.apps) * 20,
                y=100 + len(self.apps) * 20,
                width=500,
                height=400
            )
            app.window_id = win.id

        # Start process if process manager available
        if self.process_mgr:
            self.process_mgr.start_process(f"app-{app.name}", 128)

        app.status = "RUNNING"

        return {
            "app_id": app_id,
            "name": app.name,
            "status": app.status,
            "window_id": app.window_id
        }

    def close_app(self, app_id: str) -> Dict:
        """Close an application."""
        if app_id not in self.apps:
            return {"app_id": app_id, "error": "App not found"}

        app = self.apps[app_id]
        app.status = "CLOSED"

        # Close window if it exists
        if app.window_id and self.wm:
            self.wm.destroy_window(app.window_id)

        return {
            "app_id": app_id,
            "name": app.name,
            "status": app.status
        }

    def list_apps(self) -> Dict:
        """List all applications."""
        apps = []
        for app_id, app in self.apps.items():
            apps.append({
                "app_id": app.app_id,
                "name": app.name,
                "type": app.type,
                "status": app.status,
                "window_id": app.window_id
            })

        return {
            "apps": apps,
            "count": len(apps)
        }

    def get_app(self, app_id: str) -> Optional[VirtualApp]:
        return self.apps.get(app_id)

    def get_stats(self) -> Dict:
        """Get app runtime statistics."""
        running = sum(1 for a in self.apps.values() if a.status == "RUNNING")
        return {
            "total_apps": len(self.apps),
            "running_apps": running
        }
