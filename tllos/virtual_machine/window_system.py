#!/usr/bin/env python3
"""
TLL OS Native Window System

TLL OS's own window management.
No OS native window API, no Qt, no SDL.
Pure Python + numpy.
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np

from .framebuffer import TLLFramebuffer


@dataclass
class TLLWindow:
    """TLL OS Native Window Object."""
    id: str
    title: str
    x: int = 0
    y: int = 0
    width: int = 400
    height: int = 300
    z_index: int = 0
    visible: bool = True
    focused: bool = False
    minimized: bool = False
    state: str = "NORMAL"  # NORMAL / MINIMIZED / MAXIMIZED

    def __post_init__(self):
        # Each window has its own pixel buffer
        self.buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.frame_hash: Optional[str] = None

    def clear(self, r: int = 40, g: int = 50, b: int = 65):
        """Clear window buffer."""
        self.buffer[:] = [r, g, b]

    def fill_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int):
        """Fill rectangle in window."""
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(self.width, x + w)
        y2 = min(self.height, y + h)
        if x1 < x2 and y1 < y2:
            self.buffer[y1:y2, x1:x2] = [r, g, b]

    def draw_border(self, r: int = 80, g: int = 100, b: int = 120, thickness: int = 1):
        """Draw window border."""
        for t in range(thickness):
            self.fill_rect(t, t, self.width - 2*t, 1, r, g, b)  # top
            self.fill_rect(t, self.height - 1 - t, self.width - 2*t, 1, r, g, b)  # bottom
            self.fill_rect(t, t, 1, self.height - 2*t, r, g, b)  # left
            self.fill_rect(self.width - 1 - t, t, 1, self.height - 2*t, r, g, b)  # right

    def commit(self):
        """Hash window buffer."""
        self.frame_hash = hashlib.sha256(self.buffer.tobytes()).hexdigest()[:12]


class TLLWindowManager:
    """TLL OS Native Window Manager."""

    def __init__(self, desktop: TLLFramebuffer):
        self.desktop = desktop
        self.windows: List[TLLWindow] = []
        self.focused_window: Optional[TLLWindow] = None
        self.next_z_index = 0
        self.next_window_id = 0

    def create_window(self, title: str, x: int = 50, y: int = 50,
                      width: int = 400, height: int = 300) -> TLLWindow:
        """Create a new window."""
        self.next_window_id += 1
        window = TLLWindow(
            id=f"win-{self.next_window_id}",
            title=title,
            x=x, y=y, width=width, height=height,
            z_index=self.next_z_index
        )
        self.next_z_index += 1
        window.clear()
        window.draw_border()
        self.windows.append(window)
        self.focus_window(window)
        return window

    def destroy_window(self, window_id: str) -> bool:
        """Destroy a window."""
        for i, w in enumerate(self.windows):
            if w.id == window_id:
                self.windows.pop(i)
                if self.focused_window and self.focused_window.id == window_id:
                    self.focused_window = self.windows[-1] if self.windows else None
                return True
        return False

    def move_window(self, window_id: str, x: int, y: int) -> bool:
        """Move window to new position."""
        for w in self.windows:
            if w.id == window_id:
                w.x = x
                w.y = y
                return True
        return False

    def resize_window(self, window_id: str, width: int, height: int) -> bool:
        """Resize window."""
        for w in self.windows:
            if w.id == window_id:
                w.width = width
                w.height = height
                # Resize buffer
                new_buffer = np.zeros((height, width, 3), dtype=np.uint8)
                h = min(w.buffer.shape[0], height)
                wd = min(w.buffer.shape[1], width)
                new_buffer[:h, :wd] = w.buffer[:h, :wd]
                w.buffer = new_buffer
                return True
        return False

    def focus_window(self, window: TLLWindow):
        """Focus a window (bring to front)."""
        for w in self.windows:
            w.focused = False
        window.focused = True
        window.z_index = self.next_z_index
        self.next_z_index += 1
        self.focused_window = window

    def get_windows_sorted(self) -> List[TLLWindow]:
        """Get windows sorted by z-index (back to front)."""
        return sorted(self.windows, key=lambda w: w.z_index)

    def get_window_count(self) -> int:
        return len(self.windows)


class TLLCompositor:
    """TLL OS Compositor - composites window buffers into desktop."""

    def __init__(self, window_manager: TLLWindowManager):
        self.wm = window_manager
        self.frame_count = 0

    def composite(self) -> Dict:
        """Composite all windows into desktop framebuffer."""
        desktop = self.wm.desktop

        # Clear desktop with wallpaper color
        desktop.clear(20, 25, 35)

        # Draw windows back-to-front
        for window in self.wm.get_windows_sorted():
            if not window.visible or window.minimized:
                continue

            # Composite window buffer onto desktop
            wh, ww = window.buffer.shape[:2]

            # Calculate overlap region
            dx1 = max(0, window.x)
            dy1 = max(0, window.y)
            dx2 = min(desktop.width, window.x + ww)
            dy2 = min(desktop.height, window.y + wh)

            if dx1 < dx2 and dy1 < dy2:
                # Source region in window buffer
                sx1 = dx1 - window.x
                sy1 = dy1 - window.y
                sx2 = sx1 + (dx2 - dx1)
                sy2 = sy1 + (dy2 - dy1)

                # Copy window pixels to desktop
                desktop.buffer[dy1:dy2, dx1:dx2] = window.buffer[sy1:sy2, sx1:sx2]

        # Commit desktop
        result = desktop.commit()
        self.frame_count += 1
        result["frame"] = self.frame_count
        result["windows"] = self.wm.get_window_count()

        return result
