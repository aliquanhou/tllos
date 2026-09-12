#!/usr/bin/env python3
"""
TLL OS Virtual Machine Boot Sequence

TLL OS's own boot process, not Windows boot.
Pure Python OS-level abstraction.
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .virtual_hardware import VirtualHardware
from .window_manager import TLLWindowManager
from .renderer import TLLRenderer, TLLDisplayBuffer


@dataclass
class BootStep:
    """A boot step."""
    step: int
    name: str
    status: str = "PENDING"
    duration_ms: float = 0.0


class TLLOSVirtualMachine:
    """TLL OS Virtual Machine - self-contained desktop OS."""

    def __init__(self):
        self.hardware = VirtualHardware()
        self.window_manager: Optional[TLLWindowManager] = None
        self.renderer: Optional[TLLRenderer] = None
        self.display_buffer: Optional[TLLDisplayBuffer] = None
        self.boot_steps: List[BootStep] = []
        self.boot_time: Optional[float] = None
        self.state: str = "POWERED_OFF"

    def boot(self) -> Dict:
        """TLL OS Boot Sequence."""
        self.boot_time = time.time()
        self.state = "BOOTING"

        # Step 1: Hardware Boot
        self._add_step(1, "TLL OS Virtual Hardware")
        hw_result = self.hardware.boot()
        self._complete_step(1, "OK")

        # Step 2: Display Subsystem
        self._add_step(2, "Display Subsystem")
        self.window_manager = TLLWindowManager(self.hardware.display)
        self.renderer = TLLRenderer(self.hardware.display, self.window_manager)
        self.display_buffer = TLLDisplayBuffer(self.hardware.display)
        self._complete_step(2, "OK")

        # Step 3: Window Manager
        self._add_step(3, "Window Manager")
        self.window_manager.create_window(
            "TLL OS Desktop",
            x=0, y=0,
            width=self.hardware.display.width,
            height=self.hardware.display.height
        )
        self._complete_step(3, "OK")

        # Step 4: Renderer
        self._add_step(4, "Renderer")
        render_result = self.display_buffer.commit(self.renderer)
        self._complete_step(4, "OK")

        # Step 5: Agent Core
        self._add_step(5, "Agent Core")
        self.hardware.memory.alloc("agent_brain", 256)
        self._complete_step(5, "OK")

        # Step 6: Desktop Ready
        self._add_step(6, "Desktop Ready")
        self.state = "DESKTOP_READY"
        self._complete_step(6, "OK")

        return {
            "os": "TLL OS Virtual Machine",
            "version": "0.1.0",
            "state": self.state,
            "boot_time_s": round(time.time() - self.boot_time, 3),
            "hardware": hw_result,
            "render": render_result,
            "windows": self.window_manager.get_windows() if self.window_manager else [],
            "boot_steps": [
                {"step": s.step, "name": s.name, "status": s.status,
                 "ms": round(s.duration_ms, 1)}
                for s in self.boot_steps
            ]
        }

    def shutdown(self) -> Dict:
        """TLL OS Shutdown."""
        self.state = "SHUTTING_DOWN"
        result = self.hardware.shutdown()
        self.state = "POWERED_OFF"
        return {
            "os": "TLL OS",
            "state": self.state,
            "hardware": result
        }

    def _add_step(self, step: int, name: str):
        self.boot_steps.append(BootStep(step=step, name=name))

    def _complete_step(self, step: int, status: str):
        for s in self.boot_steps:
            if s.step == step:
                s.status = status
                # Estimate duration
                s.duration_ms = 5.0
                break
