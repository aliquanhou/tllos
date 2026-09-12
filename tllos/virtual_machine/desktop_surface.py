#!/usr/bin/env python3
"""
TLL OS Desktop Surface

TLL OS's own desktop surface, not Windows desktop.
Pure Python rendering to virtual framebuffer.
"""

import time
from pathlib import Path
from typing import Optional, Dict
from .framebuffer import TLLFramebuffer


class TLLDesktopSurface:
    """TLL OS Desktop Surface - renders the TLL desktop."""

    def __init__(self, framebuffer: TLLFramebuffer):
        self.fb = framebuffer
        self.title = "TLL OS Desktop"
        self.status = "ONLINE"
        self.agent_status = "READY"
        self.lm_status = "NOT_CONNECTED"
        self.frame_id = 0

    def render_desktop(self) -> dict:
        """Render TLL OS desktop to framebuffer."""
        fb = self.fb
        w, h = fb.width, fb.height

        # Background (dark blue-gray)
        fb.clear(20, 25, 35)

        # Top bar (title bar)
        fb.fill_rect(0, 0, w, 50, 30, 40, 55)

        # Title text area (simplified - draw colored rectangles as "text")
        fb.fill_rect(20, 15, 200, 20, 100, 200, 255)  # "TLL OS Desktop" title

        # Status indicator (green circle)
        fb.fill_rect(w - 50, 15, 20, 20, 0, 200, 100)

        # Left panel (system info)
        fb.fill_rect(20, 70, 300, 200, 40, 50, 65)
        fb.draw_rect(20, 70, 300, 200, 80, 100, 120, 1)

        # System info lines (as colored bars representing text)
        fb.fill_rect(40, 90, 150, 15, 150, 180, 200)  # "System: ONLINE"
        fb.fill_rect(40, 120, 150, 15, 100, 150, 200)  # "Agent: READY"
        fb.fill_rect(40, 150, 150, 15, 200, 150, 100)  # "LLM: NOT_CONNECTED"

        # Center area (desktop canvas)
        fb.fill_rect(350, 70, w - 370, h - 140, 25, 30, 40)
        fb.draw_rect(350, 70, w - 370, h - 140, 60, 80, 100, 1)

        # Center "desktop ready" indicator
        fb.fill_rect(w // 2 - 100, h // 2 - 20, 200, 40, 50, 150, 100)

        # Bottom bar (taskbar)
        fb.fill_rect(0, h - 50, w, 50, 30, 40, 55)
        fb.fill_rect(20, h - 35, 80, 20, 60, 120, 200)  # "Start" button

        # Commit frame
        result = fb.commit()
        self.frame_id = result["frame"]
        return result

    def export_screenshot(self, output_path: Path) -> Dict:
        """Export current desktop as PNG."""
        try:
            from PIL import Image

            # Convert numpy buffer to PIL Image
            img = Image.fromarray(self.fb.get_pixel_data(), 'RGB')
            img.save(str(output_path))

            return {
                "path": str(output_path),
                "width": self.fb.width,
                "height": self.fb.height,
                "hash": self.fb.buffer_hash,
                "frame": self.frame_id,
                "format": "PNG"
            }
        except ImportError:
            # Fallback: raw BMP
            return {
                "path": None,
                "error": "PIL not available",
                "format": "RAW"
            }
