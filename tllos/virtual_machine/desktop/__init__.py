#!/usr/bin/env python3
"""
TLL OS Desktop Package

Native AI-native desktop environment.
"""

from .theme.colors import TLLTheme
from .desktop_surface import TLLDesktopSurface, DesktopPanel

__all__ = [
    "TLLTheme",
    "TLLDesktopSurface",
    "DesktopPanel",
]
