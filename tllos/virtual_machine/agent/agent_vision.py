#!/usr/bin/env python3
"""
TLL OS Agent Vision

Agent's ability to observe its own digital world.
"""

import time
from typing import Dict, List, Optional
from ..window_system import TLLWindowManager, TLLCompositor


class TLLAgentVision:
    """TLL OS Agent Vision - observe the digital world."""

    def __init__(self, window_manager: TLLWindowManager, compositor: TLLCompositor):
        self.wm = window_manager
        self.compositor = compositor
        self.observation_count = 0

    def observe_world(self) -> Dict:
        """Observe current state of the digital world."""
        self.observation_count += 1

        # Get window list
        windows = []
        for w in self.wm.get_windows_sorted():
            windows.append({
                "id": w.id,
                "title": w.title,
                "x": w.x, "y": w.y,
                "width": w.width, "height": w.height,
                "focused": w.focused,
                "visible": w.visible
            })

        # Get compositor state
        comp_result = self.compositor.composite()

        return {
            "observation_id": f"obs-{self.observation_count}",
            "timestamp": time.time(),
            "desktop": {
                "resolution": f"{self.wm.desktop.width}x{self.wm.desktop.height}",
                "frame_hash": comp_result["hash"],
                "frame": comp_result["frame"]
            },
            "windows": windows,
            "window_count": len(windows),
            "focused_window": self.wm.focused_window.title if self.wm.focused_window else None,
            "state": "OBSERVED"
        }

    def get_observation_history(self) -> Dict:
        """Get observation statistics."""
        return {
            "total_observations": self.observation_count,
            "current_windows": len(self.wm.windows)
        }
