#!/usr/bin/env python3
"""
TLL OS Text Rendering Engine

Pure Python text rendering via PIL.
No Windows Font API, no Qt, no WebView.
"""

import hashlib
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .framebuffer import TLLFramebuffer


class TLLTextRenderer:
    """TLL OS Text Renderer - renders text to framebuffer."""

    def __init__(self, framebuffer: TLLFramebuffer):
        self.fb = framebuffer
        self._font_cache = {}
        self._load_default_font()

    def _load_default_font(self):
        """Load default font (English + Chinese if available)."""
        # Try to find a font that supports Chinese
        font_paths = [
            # Common Windows fonts (but we're not using Windows API, just file)
            "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei
            "C:/Windows/Fonts/simhei.ttf",  # SimHei
            "C:/Windows/Fonts/arial.ttf",  # Arial fallback
        ]

        self.font_small = None
        self.font_medium = None
        self.font_large = None

        for path in font_paths:
            if Path(path).exists():
                try:
                    self.font_small = ImageFont.truetype(path, 12)
                    self.font_medium = ImageFont.truetype(path, 16)
                    self.font_large = ImageFont.truetype(path, 24)
                    self.font_path = path
                    break
                except Exception:
                    continue

        # Fallback to PIL default
        if self.font_small is None:
            self.font_small = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_large = ImageFont.load_default()
            self.font_path = "PIL-default"

    def draw_text(self, x: int, y: int, text: str,
                  r: int = 255, g: int = 255, b: int = 255,
                  size: str = "medium") -> dict:
        """Draw text at position on framebuffer."""
        # Select font
        if size == "small":
            font = self.font_small
        elif size == "large":
            font = self.font_large
        else:
            font = self.font_medium

        # Create a PIL image for text rendering
        # First, measure text
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        if text_w == 0 or text_h == 0:
            return {"text": text, "width": 0, "height": 0}

        # Create text image
        text_img = Image.new('RGB', (text_w + 2, text_h + 2), (0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        text_draw.text((1, 1), text, fill=(r, g, b), font=font)

        # Convert to numpy array
        text_array = np.array(text_img)

        # Blit to framebuffer
        h, w = text_array.shape[:2]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(self.fb.width, x + w)
        y2 = min(self.fb.height, y + h)

        if x1 < x2 and y1 < y2:
            # Only copy non-black pixels (transparent background)
            region = text_array[:y2-y1, :x2-x1]
            mask = region.sum(axis=2) > 0  # non-black pixels
            self.fb.buffer[y1:y2, x1:x2][mask] = region[mask]

        # Hash the rendered text
        text_hash = hashlib.sha256(text.encode() + str(font.size).encode()).hexdigest()[:12]

        return {
            "text": text,
            "width": text_w,
            "height": text_h,
            "x": x, "y": y,
            "hash": text_hash,
            "font": self.font_path
        }

    def draw_text_center(self, cx: int, y: int, text: str,
                         r: int = 255, g: int = 255, b: int = 255,
                         size: str = "medium") -> dict:
        """Draw centered text."""
        # Measure first
        if size == "small":
            font = self.font_small
        elif size == "large":
            font = self.font_large
        else:
            font = self.font_medium

        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]

        x = cx - text_w // 2
        return self.draw_text(x, y, text, r, g, b, size)
