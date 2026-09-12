#!/usr/bin/env python3
"""
TLL OS Desktop Package

Execution Desktop with full agent pipeline.
"""

from .theme.theme import TLLFlatTheme
from .layout.layout_manager import TLLLayoutManager, PanelRect
from .desktop_surface import TLLExecutionDesktop

__all__ = [
    "TLLFlatTheme",
    "TLLLayoutManager",
    "PanelRect",
    "TLLExecutionDesktop",
]
