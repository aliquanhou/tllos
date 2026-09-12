#!/usr/bin/env python3
"""
TLL OS Flat Theme Engine

Flat, clean design system for TLL OS.
"""


class TLLFlatTheme:
    """TLL OS Flat Design System."""

    # Colors
    TLL_BACKGROUND = (5, 8, 18)       # #050812
    TLL_PANEL = (16, 24, 39)          # #101827
    TLL_PANEL_BORDER = (30, 45, 70)   # #1E2D46
    TLL_PRIMARY = (0, 229, 255)       # #00E5FF
    TLL_ALIVE = (0, 255, 136)         # #00FF88
    TLL_WARNING = (255, 204, 0)       # #FFCC00
    TLL_DANGER = (255, 51, 68)        # #FF3344
    TLL_CREATION = (255, 209, 102)    # #FFD166
    TLL_TEXT_PRIMARY = (230, 240, 255) # #E6F0FF
    TLL_TEXT_SECONDARY = (140, 160, 190) # #8CA0BE
    TLL_TEXT_MUTED = (90, 110, 140)   # #5A6E8C

    # Layout
    MARGIN = 24
    PANEL_PADDING = 16
    TITLE_BAR_HEIGHT = 48
    PANEL_SPACING = 16
    HALF_PANEL_WIDTH_OFFSET = 0  # For two-column layouts

    @classmethod
    def get_palette(cls) -> dict:
        return {
            "background": cls.TLL_BACKGROUND,
            "panel": cls.TLL_PANEL,
            "panel_border": cls.TLL_PANEL_BORDER,
            "primary": cls.TLL_PRIMARY,
            "alive": cls.TLL_ALIVE,
            "warning": cls.TLL_WARNING,
            "danger": cls.TLL_DANGER,
            "creation": cls.TLL_CREATION,
            "text_primary": cls.TLL_TEXT_PRIMARY,
            "text_secondary": cls.TLL_TEXT_SECONDARY,
            "text_muted": cls.TLL_TEXT_MUTED
        }

    @classmethod
    def get_layout(cls) -> dict:
        return {
            "margin": cls.MARGIN,
            "panel_padding": cls.PANEL_PADDING,
            "title_bar_height": cls.TITLE_BAR_HEIGHT,
            "panel_spacing": cls.PANEL_SPACING
        }
