#!/usr/bin/env python3
"""
TLL OS Virtual Machine Package

TLL OS's own virtual hardware and desktop runtime.
No dependency on Windows API or external GUI frameworks.
"""

from .virtual_hardware import VirtualHardware, VirtualCPU, VirtualMemory, VirtualDisplay, VirtualInput, VirtualStorage
from .window_manager import TLLWindowManager, TLLWindow
from .renderer import TLLRenderer, TLLDisplayBuffer, DisplayFrame
from .os import TLLOSVirtualMachine

__version__ = "0.1.0"
__all__ = [
    "VirtualHardware", "VirtualCPU", "VirtualMemory",
    "VirtualDisplay", "VirtualInput", "VirtualStorage",
    "TLLWindowManager", "TLLWindow",
    "TLLRenderer", "TLLDisplayBuffer", "DisplayFrame",
    "TLLOSVirtualMachine",
]
