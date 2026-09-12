#!/usr/bin/env python3
"""
TLL OS Window Manager

TLL OS's own window management, not Windows HWND.
Pure Python abstraction layer.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .virtual_hardware import VirtualDisplay


@dataclass
class TLLWindow:
    """TLL OS native window."""
    id: str
    title: str
    x: int = 0
    y: int = 0
    width: int = 800
    height: int = 600
    visible: bool = True
    focused: bool = False
    z_order: int = 0


class TLLWindowManager:
    """TLL OS Window Manager."""

    def __init__(self, display: VirtualDisplay):
        self.display = display
        self.windows: List[TLLWindow] = []
        self.focused_window: Optional[TLLWindow] = None
        self.next_z_order = 0
        self.window_count = 0

    def create_window(self, title: str, x: int = 100, y: int = 100,
                      width: int = 800, height: int = 600) -> TLLWindow:
        """Create a TLL OS window."""
        self.window_count += 1
        window = TLLWindow(
            id=f"win-{self.window_count}",
            title=title,
            x=x, y=y, width=width, height=height,
            z_order=self.next_z_order
        )
        self.next_z_order += 1
        self.windows.append(window)
        self.focus_window(window)
        return window

    def focus_window(self, window: TLLWindow):
        """Focus a window."""
        for w in self.windows:
            w.focused = False
        window.focused = True
        window.z_order = self.next_z_order
        self.next_z_order += 1
        self.focused_window = window

    def close_window(self, window_id: str) -> bool:
        """Close a window."""
        for i, w in enumerate(self.windows):
            if w.id == window_id:
                self.windows.pop(i)
                if self.focused_window and self.focused_window.id == window_id:
                    self.focused_window = self.windows[-1] if self.windows else None
                return True
        return False

    def get_windows(self) -> List[Dict]:
        """Get window list."""
        return [
            {"id": w.id, "title": w.title, "x": w.x, "y": w.y,
             "width": w.width, "height": w.height, "focused": w.focused}
            for w in sorted(self.windows, key=lambda x: x.z_order)
        ]
