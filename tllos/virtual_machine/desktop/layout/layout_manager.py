#!/usr/bin/env python3
"""
TLL OS Desktop Layout Engine

Flexible panel layout management.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass

from ..theme.theme import TLLFlatTheme


@dataclass
class PanelRect:
    """Panel rectangle."""
    x: int
    y: int
    width: int
    height: int
    title: str = ""


class TLLLayoutManager:
    """TLL OS Desktop Layout Manager."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.margin = TLLFlatTheme.MARGIN
        self.spacing = TLLFlatTheme.PANEL_SPACING
        self.title_bar_height = TLLFlatTheme.TITLE_BAR_HEIGHT

    def get_content_area(self) -> Tuple[int, int, int, int]:
        """Get content area (below title bar)."""
        x = self.margin
        y = self.title_bar_height + self.margin
        width = self.screen_width - 2 * self.margin
        height = self.screen_height - y - self.margin
        return x, y, width, height

    def layout_single_column(self, panel_heights: List[int]) -> List[PanelRect]:
        """Layout panels in single column."""
        content_x, content_y, content_width, _ = self.get_content_area()
        panels = []
        current_y = content_y

        for height in panel_heights:
            panels.append(PanelRect(
                x=content_x,
                y=current_y,
                width=content_width,
                height=height
            ))
            current_y += height + self.spacing

        return panels

    def layout_two_column(self, left_heights: List[int],
                          right_heights: List[int]) -> Tuple[List[PanelRect], List[PanelRect]]:
        """Layout panels in two columns."""
        content_x, content_y, content_width, _ = self.get_content_area()
        col_width = (content_width - self.spacing) // 2

        left_panels = []
        right_panels = []

        # Left column
        current_y = content_y
        for height in left_heights:
            left_panels.append(PanelRect(
                x=content_x,
                y=current_y,
                width=col_width,
                height=height
            ))
            current_y += height + self.spacing

        # Right column
        current_y = content_y
        right_x = content_x + col_width + self.spacing
        for height in right_heights:
            right_panels.append(PanelRect(
                x=right_x,
                y=current_y,
                width=col_width,
                height=height
            ))
            current_y += height + self.spacing

        return left_panels, right_panels

    def layout_full_desktop(self) -> Dict[str, PanelRect]:
        """Layout all desktop panels."""
        # Agent Panel (full width)
        agent_panel = PanelRect(
            x=self.margin,
            y=self.title_bar_height + self.margin,
            width=self.screen_width - 2 * self.margin,
            height=80,
            title="AGENT"
        )

        # Two columns: Vision + Memory
        col_width = (self.screen_width - 2 * self.margin - self.spacing) // 2
        two_col_y = agent_panel.y + agent_panel.height + self.spacing

        vision_panel = PanelRect(
            x=self.margin,
            y=two_col_y,
            width=col_width,
            height=120,
            title="VISION"
        )

        memory_panel = PanelRect(
            x=self.margin + col_width + self.spacing,
            y=two_col_y,
            width=col_width,
            height=120,
            title="MEMORY"
        )

        # Capability Panel (full width)
        cap_y = two_col_y + 120 + self.spacing
        capability_panel = PanelRect(
            x=self.margin,
            y=cap_y,
            width=self.screen_width - 2 * self.margin,
            height=70,
            title="CAPABILITY"
        )

        # World Model Panel (full width)
        world_y = cap_y + 70 + self.spacing
        world_panel = PanelRect(
            x=self.margin,
            y=world_y,
            width=self.screen_width - 2 * self.margin,
            height=60,
            title="WORLD MODEL"
        )

        # Creation Space Panel (full width)
        creation_y = world_y + 60 + self.spacing
        creation_panel = PanelRect(
            x=self.margin,
            y=creation_y,
            width=self.screen_width - 2 * self.margin,
            height=60,
            title="CREATION SPACE"
        )

        # Owner Command Panel (full width)
        cmd_y = creation_y + 60 + self.spacing
        command_panel = PanelRect(
            x=self.margin,
            y=cmd_y,
            width=self.screen_width - 2 * self.margin,
            height=70,
            title="OWNER COMMAND"
        )

        return {
            "agent": agent_panel,
            "vision": vision_panel,
            "memory": memory_panel,
            "capability": capability_panel,
            "world": world_panel,
            "creation": creation_panel,
            "command": command_panel
        }
