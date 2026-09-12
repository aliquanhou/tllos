#!/usr/bin/env python3
"""
TLL OS Display Buffer and Renderer

TLL OS's own rendering pipeline, not GDI/DirectX.
Pure Python abstraction.
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .virtual_hardware import VirtualDisplay
from .window_manager import TLLWindowManager, TLLWindow


@dataclass
class DisplayFrame:
    """A rendered frame in TLL OS."""
    frame_id: int
    timestamp: float
    width: int
    height: int
    pixel_count: int
    hash: str


class TLLRenderer:
    """TLL OS Renderer."""

    def __init__(self, display: VirtualDisplay, window_manager: TLLWindowManager):
        self.display = display
        self.wm = window_manager
        self.frame_count = 0
        self.frames: List[DisplayFrame] = []

    def render(self) -> DisplayFrame:
        """Render current state to display buffer."""
        self.frame_count += 1
        now = time.time()

        # Simulate rendering
        pixel_count = self.display.width * self.display.height
        render_data = f"{self.frame_count}-{now}-{self.display.width}-{self.display.height}".encode()
        frame_hash = hashlib.sha256(render_data).hexdigest()[:16]

        frame = DisplayFrame(
            frame_id=self.frame_count,
            timestamp=now,
            width=self.display.width,
            height=self.display.height,
            pixel_count=pixel_count,
            hash=frame_hash
        )
        self.frames.append(frame)

        # Keep last 100 frames
        if len(self.frames) > 100:
            self.frames = self.frames[-100:]

        return frame

    def get_fps(self) -> float:
        """Calculate FPS from recent frames."""
        if len(self.frames) < 2:
            return 0.0
        recent = self.frames[-10:]
        if len(recent) < 2:
            return 0.0
        time_diff = recent[-1].timestamp - recent[0].timestamp
        if time_diff == 0:
            return 0.0
        return len(recent) / time_diff


class TLLDisplayBuffer:
    """TLL OS Display Buffer Manager."""

    def __init__(self, display: VirtualDisplay):
        self.display = display
        self.buffer_hash: Optional[str] = None
        self.buffer_size_mb: float = 0.0

    def commit(self, renderer: TLLRenderer) -> Dict:
        """Commit rendered frame to display buffer."""
        frame = renderer.render()
        self.buffer_size_mb = (frame.width * frame.height * 4) / (1024 * 1024)
        self.buffer_hash = frame.hash

        return {
            "frame_id": frame.frame_id,
            "resolution": f"{frame.width}x{frame.height}",
            "hash": frame.hash,
            "buffer_mb": round(self.buffer_size_mb, 2),
            "fps": round(renderer.get_fps(), 1)
        }
