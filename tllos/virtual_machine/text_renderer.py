#!/usr/bin/env python3
"""
TLL OS Text Rendering Engine (Native Version)

Renders text using TLL Native Font Runtime.
No PIL font, no Windows font files.
Pure Python bitmap rendering.
"""

import hashlib
from typing import Tuple, Optional
import numpy as np
from pathlib import Path

from .framebuffer import TLLFramebuffer
from .fonts.tll_font import TLLFont


class TLLTextRenderer:
    """TLL OS Text Renderer - Native font rendering."""

    def __init__(self, framebuffer: TLLFramebuffer):
        self.fb = framebuffer
        self.font = TLLFont()
        self.font_name = self.font.font_name

    def draw_text(self, x: int, y: int, text: str,
                  r: int = 255, g: int = 255, b: int = 255,
                  size: str = "medium") -> dict:
        """Draw text at position on framebuffer using native font."""
        cursor_x = x
        cursor_y = y

        for char in text:
            glyph = self.font.get_glyph(char)
            if glyph is None:
                cursor_x += 9  # Skip unknown chars
                continue

            gh, gw = glyph.shape

            # Scale based on size
            if size == "small":
                scale = 1
            elif size == "large":
                scale = 2
            else:
                scale = 1

            # Draw glyph pixels
            for gy in range(gh):
                for gx in range(gw):
                    if glyph[gy, gx]:
                        # Scale up if needed
                        for sy in range(scale):
                            for sx in range(scale):
                                px = cursor_x + gx * scale + sx
                                py = cursor_y + gy * scale + sy
                                if 0 <= px < self.fb.width and 0 <= py < self.fb.height:
                                    self.fb.buffer[py, px] = [r, g, b]

            cursor_x += gw * scale + 1  # 1px spacing

        # Calculate text hash
        text_hash = hashlib.sha256(text.encode() + size.encode()).hexdigest()[:12]

        # Calculate actual width
        actual_width = 0
        for char in text:
            glyph = self.font.get_glyph(char)
            if glyph is not None:
                gh, gw = glyph.shape
                scale = 2 if size == "large" else 1
                actual_width += gw * scale + 1

        return {
            "text": text,
            "width": actual_width,
            "height": 16,
            "x": x, "y": y,
            "hash": text_hash,
            "font": self.font_name
        }

    def draw_text_center(self, cx: int, y: int, text: str,
                         r: int = 255, g: int = 255, b: int = 255,
                         size: str = "medium") -> dict:
        """Draw centered text."""
        width, _ = self.font.get_text_dimensions(text)
        if size == "large":
            width *= 2
        x = cx - width // 2
        return self.draw_text(x, y, text, r, g, b, size)
