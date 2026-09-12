#!/usr/bin/env python3
"""
TLL OS Text Rendering Engine

Renders text on framebuffer.
- ASCII: built-in 5x7 bitmap font
- Chinese: PIL + system font (msyh.ttc)
"""

import hashlib
from typing import Tuple, Optional
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from .framebuffer import TLLFramebuffer
from .fonts.tll_font import TLLFont


class TLLTextRenderer:
    """TLL OS Text Renderer - mixed ASCII bitmap + Chinese PIL."""

    def __init__(self, framebuffer: TLLFramebuffer):
        self.fb = framebuffer
        self.font = TLLFont()
        self.font_name = self.font.font_name

        # Chinese font via PIL
        self._chinese_font = None
        self._chinese_font_large = None
        self._init_chinese_font()

    def _init_chinese_font(self):
        """Load Chinese font via PIL."""
        try:
            # Try Windows system fonts
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf",
                "C:/Windows/Fonts/simsun.ttc",
            ]
            for fp in font_paths:
                if Path(fp).exists():
                    self._chinese_font = ImageFont.truetype(fp, 14)
                    self._chinese_font_large = ImageFont.truetype(fp, 20)
                    break
        except Exception:
            pass

    def draw_text(self, x: int, y: int, text: str,
                  r: int = 255, g: int = 255, b: int = 255,
                  size: str = "medium") -> dict:
        """Draw text at position on framebuffer."""
        cursor_x = x

        for char in text:
            # Check if Chinese
            if ord(char) > 127 and self._chinese_font:
                # Render Chinese via PIL
                self._draw_chinese_char(cursor_x, y, char, r, g, b, size)
                cursor_x += 16  # Chinese char width
            else:
                # ASCII via built-in font
                glyph = self.font.get_glyph(char)
                if glyph is None:
                    cursor_x += 9
                    continue

                gh, gw = glyph.shape
                scale = 2 if size == "large" else 1

                for gy in range(gh):
                    for gx in range(gw):
                        if glyph[gy, gx]:
                            for sy in range(scale):
                                for sx in range(scale):
                                    px = cursor_x + gx * scale + sx
                                    py = y + gy * scale + sy
                                    if 0 <= px < self.fb.width and 0 <= py < self.fb.height:
                                        self.fb.buffer[py, px] = [r, g, b]

                cursor_x += gw * scale + 1

        text_hash = hashlib.sha256(text.encode() + size.encode()).hexdigest()[:12]
        return {"text": text, "hash": text_hash}

    def _draw_chinese_char(self, x: int, y: int, char: str,
                           r: int, g: int, b: int, size: str):
        """Draw a single Chinese character via PIL."""
        font = self._chinese_font_large if size == "large" else self._chinese_font
        if not font:
            return

        # Create small PIL image for this character
        img = Image.new('L', (16, 16), 0)
        draw = ImageDraw.Draw(img)
        draw.text((0, -1), char, fill=255, font=font)

        # Copy pixels to framebuffer
        pixels = np.array(img)
        for py in range(16):
            for px in range(16):
                if pixels[py, px] > 128:
                    fb_x = x + px
                    fb_y = y + py
                    if 0 <= fb_x < self.fb.width and 0 <= fb_y < self.fb.height:
                        self.fb.buffer[fb_y, fb_x] = [r, g, b]

    def draw_text_center(self, cx: int, y: int, text: str,
                         r: int = 255, g: int = 255, b: int = 255,
                         size: str = "medium") -> dict:
        """Draw centered text."""
        width, _ = self.font.get_text_dimensions(text)
        if size == "large":
            width *= 2
        x = cx - width // 2
        return self.draw_text(x, y, text, r, g, b, size)
