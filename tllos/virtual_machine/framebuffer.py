#!/usr/bin/env python3
"""
TLL OS Virtual Framebuffer

Pixel-level framebuffer for TLL OS.
Pure Python + numpy, no OS dependency.
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional, Tuple
import numpy as np


@dataclass
class TLLFramebuffer:
    """TLL OS Virtual Framebuffer (pixel-level)."""
    width: int = 1920
    height: int = 1080
    bpp: int = 3  # RGB, 24-bit

    def __post_init__(self):
        # Initialize framebuffer with black
        self.buffer = np.zeros((self.height, self.width, self.bpp), dtype=np.uint8)
        self.frame_count = 0
        self.buffer_hash: Optional[str] = None
        self.updated_at: Optional[float] = None

    def clear(self, r: int = 0, g: int = 0, b: int = 0):
        """Clear framebuffer with color."""
        self.buffer[:] = [r, g, b]

    def put_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """Draw a single pixel."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y, x] = [r, g, b]

    def fill_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int):
        """Fill a rectangle."""
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(self.width, x + w)
        y2 = min(self.height, y + h)
        if x1 < x2 and y1 < y2:
            self.buffer[y1:y2, x1:x2] = [r, g, b]

    def draw_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, thickness: int = 1):
        """Draw a rectangle border."""
        for t in range(thickness):
            self.fill_rect(x + t, y + t, w - 2*t, 1, r, g, b)  # top
            self.fill_rect(x + t, y + h - 1 - t, w - 2*t, 1, r, g, b)  # bottom
            self.fill_rect(x + t, y + t, 1, h - 2*t, r, g, b)  # left
            self.fill_rect(x + w - 1 - t, y + t, 1, h - 2*t, r, g, b)  # right

    def commit(self) -> dict:
        """Commit framebuffer and compute hash."""
        self.frame_count += 1
        self.updated_at = time.time()
        # Hash the buffer data
        self.buffer_hash = hashlib.sha256(self.buffer.tobytes()).hexdigest()[:16]
        return {
            "frame": self.frame_count,
            "resolution": f"{self.width}x{self.height}",
            "hash": self.buffer_hash,
            "timestamp": self.updated_at
        }

    def get_pixel_data(self) -> np.ndarray:
        """Get raw pixel data."""
        return self.buffer.copy()
