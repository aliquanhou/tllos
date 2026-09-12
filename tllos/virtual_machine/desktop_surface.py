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
from .text_renderer import TLLTextRenderer


class TLLDesktopSurface:
    """TLL OS Desktop Surface - renders the TLL desktop."""

    def __init__(self, framebuffer: TLLFramebuffer):
        self.fb = framebuffer
        self.text_renderer = TLLTextRenderer(framebuffer)
        self.title = "TLL OS Desktop"
        self.status = "ONLINE"
        self.agent_status = "READY"
        self.lm_status = "NOT_CONNECTED"
        self.frame_id = 0

    def render_desktop(self) -> dict:
        """Render TLL OS desktop to framebuffer."""
        fb = self.fb
        tr = self.text_renderer
        w, h = fb.width, fb.height

        # Background (dark blue-gray)
        fb.clear(20, 25, 35)

        # Top bar (title bar)
        fb.fill_rect(0, 0, w, 50, 30, 40, 55)

        # Title text (real text rendering)
        tr.draw_text(20, 15, "TLL OS 智能代理", 100, 200, 255, "large")

        # Status indicator (green circle as rectangle)
        fb.fill_rect(w - 50, 15, 20, 20, 0, 200, 100)
        tr.draw_text(w - 80, 18, "ONLINE", 100, 255, 150, "small")

        # Left panel (system info)
        fb.fill_rect(20, 70, 320, 250, 40, 50, 65)
        fb.draw_rect(20, 70, 320, 250, 80, 100, 120, 1)

        # System panel title
        tr.draw_text(40, 80, "系统状态", 180, 200, 220, "medium")

        # System info lines (real text)
        tr.draw_text(40, 110, "系统状态: ONLINE", 100, 200, 255, "small")
        tr.draw_text(40, 135, "智能代理: READY", 100, 180, 220, "small")
        tr.draw_text(40, 160, "LLM: NOT_CONNECTED", 220, 180, 120, "small")
        tr.draw_text(40, 185, "显示: 1920x1080", 150, 170, 190, "small")
        tr.draw_text(40, 210, "内存: 2304/4096 MB", 150, 170, 190, "small")

        # Center area (desktop canvas)
        fb.fill_rect(370, 70, w - 390, h - 140, 25, 30, 40)
        fb.draw_rect(370, 70, w - 390, h - 140, 60, 80, 100, 1)

        # Center welcome text (real text)
        tr.draw_text_center(w // 2, h // 2 - 40, "TLL OS Desktop", 100, 200, 255, "large")
        tr.draw_text_center(w // 2, h // 2, "Agent ONLINE", 100, 255, 150, "medium")
        tr.draw_text_center(w // 2, h // 2 + 30, "等待任务...", 180, 200, 220, "small")

        # Bottom bar (taskbar)
        fb.fill_rect(0, h - 50, w, 50, 30, 40, 55)
        fb.fill_rect(20, h - 35, 80, 20, 60, 120, 200)
        tr.draw_text(35, h - 32, "开始", 255, 255, 255, "small")

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
