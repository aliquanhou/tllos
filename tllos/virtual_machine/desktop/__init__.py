#!/usr/bin/env python3
"""
TLL OS Desktop Package

Real-time AI-native desktop environment.
"""

from .theme.theme import TLLFlatTheme
from .layout.layout_manager import TLLLayoutManager, PanelRect
from .desktop_surface import TLLRealityDesktop

__all__ = [
    "TLLFlatTheme",
    "TLLLayoutManager",
    "PanelRect",
    "TLLRealityDesktop",
]
