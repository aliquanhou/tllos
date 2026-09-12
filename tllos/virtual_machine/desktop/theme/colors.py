#!/usr/bin/env python3
"""
TLL OS Native Desktop Theme

TLL Design Language - Deep Space Theme.
"""


class TLLTheme:
    """TLL OS Design System - Deep Space Theme."""

    # Colors - Deep Space
    BACKGROUND = (5, 8, 18)        # #050812 - Deep space background
    PANEL = (16, 24, 39)           # #101827 - Panel background
    PANEL_BORDER = (30, 45, 70)    # #1E2D46 - Panel border
    PRIMARY = (0, 229, 255)        # #00E5FF - Primary accent (cyan)
    ALIVE = (0, 255, 136)          # #00FF88 - Success/alive (green)
    WARNING = (255, 204, 0)        # #FFCC00 - Warning (yellow)
    CRITICAL = (255, 51, 68)       # #FF3344 - Critical (red)
    TEXT_PRIMARY = (230, 240, 255) # #E6F0FF - Primary text
    TEXT_SECONDARY = (140, 160, 190) # #8CA0BE - Secondary text
    TEXT_MUTED = (90, 110, 140)    # #5A6E8C - Muted text

    # Layout
    MARGIN = 20
    PANEL_PADDING = 15
    TITLE_HEIGHT = 40
    PANEL_SPACING = 15

    @classmethod
    def get_palette(cls) -> dict:
        """Get full color palette."""
        return {
            "background": cls.BACKGROUND,
            "panel": cls.PANEL,
            "panel_border": cls.PANEL_BORDER,
            "primary": cls.PRIMARY,
            "alive": cls.ALIVE,
            "warning": cls.WARNING,
            "critical": cls.CRITICAL,
            "text_primary": cls.TEXT_PRIMARY,
            "text_secondary": cls.TEXT_SECONDARY,
            "text_muted": cls.TEXT_MUTED
        }

    @classmethod
    def get_layout(cls) -> dict:
        """Get layout constants."""
        return {
            "margin": cls.MARGIN,
            "panel_padding": cls.PANEL_PADDING,
            "title_height": cls.TITLE_HEIGHT,
            "panel_spacing": cls.PANEL_SPACING
        }
