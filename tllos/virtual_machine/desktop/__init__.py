#!/usr/bin/env python3
"""
TLL OS Desktop Package

Native AI-native desktop environment.
"""

from .theme.theme import TLLFlatTheme
from .layout.layout_manager import TLLLayoutManager, PanelRect
from .desktop_surface import TLLFlatDesktop

__all__ = [
    "TLLFlatTheme",
    "TLLLayoutManager",
    "PanelRect",
    "TLLFlatDesktop",
]
