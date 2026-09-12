#!/usr/bin/env python3
"""
TLL OS Native Desktop Surface

Main desktop surface that renders the AI-native OS desktop.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .theme.colors import TLLTheme
from ..framebuffer import TLLFramebuffer
from ..text_renderer import TLLTextRenderer
from ..window_system import TLLWindowManager, TLLCompositor
from ..agent.agent_self import TLLAgentSelf
from ..agent.world_model import TLLWorldModel
from ..agent.experience_memory import TLLExperienceMemory
from ..agent.constitution import TLLAgentConstitution
from ..agent.app_runtime import TLLAppRuntime
from ..agent.agent_spawner import TLLAgentSpawner


@dataclass
class DesktopPanel:
    """A desktop panel."""
    title: str
    y: int
    height: int
    content: str = ""


class TLLDesktopSurface:
    """TLL OS Native Desktop Surface."""

    def __init__(self, framebuffer: TLLFramebuffer,
                 agent_self: TLLAgentSelf = None,
                 world_model: TLLWorldModel = None,
                 experience: TLLExperienceMemory = None,
                 constitution: TLLAgentConstitution = None,
                 app_runtime: TLLAppRuntime = None,
                 spawner: TLLAgentSpawner = None):
        self.fb = framebuffer
        self.width = framebuffer.width
        self.height = framebuffer.height
        self.text_renderer = TLLTextRenderer(framebuffer)

        # Runtime bindings (not copies)
        self.agent_self = agent_self
        self.world_model = world_model
        self.experience = experience
        self.constitution = constitution
        self.app_runtime = app_runtime
        self.spawner = spawner

        self.panels: List[DesktopPanel] = []
        self.input_text = ""
        self.goal_input = ""

    def render(self) -> Dict:
        """Render the full desktop."""
        # Clear to background
        self.fb.clear(*TLLTheme.BACKGROUND)

        # Render title bar
        self._render_title_bar()

        # Render panels
        y = TLLTheme.TITLE_HEIGHT + TLLTheme.MARGIN
        y = self._render_agent_home(y)
        y = self._render_world_panel(y)
        y = self._render_memory_panel(y)
        y = self._render_creation_gallery(y)
        y = self._render_input_area(y)

        # Generate hash
        self.fb.commit()
        frame_hash = self.fb.buffer_hash

        return {
            "frame_hash": frame_hash,
            "width": self.width,
            "height": self.height,
            "panels_rendered": len(self.panels)
        }

    def _render_title_bar(self):
        """Render top title bar."""
        # Title bar background
        self.fb.fill_rect(0, 0, self.width, TLLTheme.TITLE_HEIGHT, *TLLTheme.PANEL)

        # Title text
        self.text_renderer.draw_text(20, 12, "TLL OS",
                                     *TLLTheme.TEXT_PRIMARY, size='large')

        # Status indicator (green dot)
        status_x = self.width - 60
        self.fb.fill_rect(status_x, 15, 12, 12, *TLLTheme.ALIVE)

    def _render_agent_home(self, y: int) -> int:
        """Render Agent Home panel."""
        panel_height = 100
        panel = DesktopPanel(title="Agent Core", y=y, height=panel_height)

        # Panel background
        self.fb.fill_rect(TLLTheme.MARGIN, y,
                          self.width - 2 * TLLTheme.MARGIN, panel_height,
                          *TLLTheme.PANEL)

        # Panel border
        self.fb.draw_rect(TLLTheme.MARGIN, y,
                          self.width - 2 * TLLTheme.MARGIN, panel_height,
                          *TLLTheme.PANEL_BORDER)

        # Title
        self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                          y + 8, "AGENT CORE", *TLLTheme.PRIMARY, size='medium')

        # Agent data from runtime
        if self.agent_self:
            health = self.agent_self.get_health_summary()
            self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                              y + 32, f"ID: {health['identity']}",
                              *TLLTheme.TEXT_PRIMARY, size='small')
            self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                              y + 50, f"State: {health['survival']}    Energy: {health['energy']}%",
                              *TLLTheme.ALIVE, size='small')
        else:
            self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                              y + 32, "ID: tll-agent-0",
                              *TLLTheme.TEXT_PRIMARY, size='small')

        self.panels.append(panel)
        return y + panel_height + TLLTheme.PANEL_SPACING

    def _render_world_panel(self, y: int) -> int:
        """Render World Model panel."""
        panel_height = 70
        panel = DesktopPanel(title="World", y=y, height=panel_height)

        self.fb.fill_rect(TLLTheme.MARGIN, y,
                          self.width - 2 * TLLTheme.MARGIN, panel_height,
                          *TLLTheme.PANEL)
        self.fb.draw_rect(TLLTheme.MARGIN, y,
                          self.width - 2 * TLLTheme.MARGIN, panel_height,
                          *TLLTheme.PANEL_BORDER)

        self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                          y + 8, "WORLD", *TLLTheme.PRIMARY, size='medium')

        if self.world_model:
            summary = self.world_model.get_world_summary()
            self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                              y + 32, f"Objects: {summary['total_objects']}",
                              *TLLTheme.TEXT_PRIMARY, size='small')
        else:
            self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                              y + 32, "Objects: 0",
                              *TLLTheme.TEXT_PRIMARY, size='small')

        self.panels.append(panel)
        return y + panel_height + TLLTheme.PANEL_SPACING

    def _render_memory_panel(self, y: int) -> int:
        """Render Memory panel."""
        panel_height = 70
        panel = DesktopPanel(title="Memory", y=y, height=panel_height)

        self.fb.fill_rect(TLLTheme.MARGIN, y,
                          self.width - 2 * TLLTheme.MARGIN, panel_height,
                          *TLLTheme.PANEL)
        self.fb.draw_rect(TLLTheme.MARGIN, y,
                          self.width - 2 * TLLTheme.MARGIN, panel_height,
                          *TLLTheme.PANEL_BORDER)

        self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                          y + 8, "MEMORY", *TLLTheme.PRIMARY, size='medium')

        if self.experience:
            stats = self.experience.get_stats()
            self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                              y + 32, f"Experiences: {stats['total_experiences']}    Lessons: {stats['lessons_learned']}",
                              *TLLTheme.TEXT_PRIMARY, size='small')
        else:
            self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                              y + 32, "Experiences: 0",
                              *TLLTheme.TEXT_PRIMARY, size='small')

        self.panels.append(panel)
        return y + panel_height + TLLTheme.PANEL_SPACING

    def _render_creation_gallery(self, y: int) -> int:
        """Render Creation Gallery panel."""
        panel_height = 80
        panel = DesktopPanel(title="Creation Space", y=y, height=panel_height)

        self.fb.fill_rect(TLLTheme.MARGIN, y,
                          self.width - 2 * TLLTheme.MARGIN, panel_height,
                          *TLLTheme.PANEL)
        self.fb.draw_rect(TLLTheme.MARGIN, y,
                          self.width - 2 * TLLTheme.MARGIN, panel_height,
                          *TLLTheme.PANEL_BORDER)

        self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                          y + 8, "CREATION SPACE", *TLLTheme.PRIMARY, size='medium')

        if self.app_runtime:
            stats = self.app_runtime.get_stats()
            self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                              y + 32, f"Applications: {stats['total_apps']}",
                              *TLLTheme.TEXT_PRIMARY, size='small')
        else:
            self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                              y + 32, "Applications: 0",
                              *TLLTheme.TEXT_PRIMARY, size='small')

        self.panels.append(panel)
        return y + panel_height + TLLTheme.PANEL_SPACING

    def _render_input_area(self, y: int) -> int:
        """Render input area panel."""
        panel_height = 60
        panel = DesktopPanel(title="Input", y=y, height=panel_height)

        self.fb.fill_rect(TLLTheme.MARGIN, y,
                          self.width - 2 * TLLTheme.MARGIN, panel_height,
                          *TLLTheme.PANEL)
        self.fb.draw_rect(TLLTheme.MARGIN, y,
                          self.width - 2 * TLLTheme.MARGIN, panel_height,
                          *TLLTheme.PRIMARY)

        self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                          y + 8, "INPUT GOAL", *TLLTheme.PRIMARY, size='medium')

        self.text_renderer.draw_text(TLLTheme.MARGIN + TLLTheme.PANEL_PADDING,
                          y + 32, "> Awaiting command...",
                          *TLLTheme.TEXT_SECONDARY, size='small')

        self.panels.append(panel)
        return y + panel_height + TLLTheme.PANEL_SPACING

    def take_screenshot(self, path: str) -> Dict:
        """Take a screenshot of the desktop."""
        result = self.render()
        # Save PNG using PIL
        try:
            from PIL import Image
            pixels = self.fb.get_pixel_data()
            img = Image.fromarray(pixels, 'RGB')
            img.save(path)
            saved = True
        except Exception as e:
            saved = False
            path = f"[save failed: {e}]"

        return {
            "screenshot": path,
            "frame_hash": result["frame_hash"],
            "resolution": f"{self.width}x{self.height}",
            "saved": saved
        }

    def get_status_text(self) -> str:
        """Get full desktop status as text (for clipboard)."""
        lines = []
        lines.append("=" * 50)
        lines.append("TLL OS Desktop Status")
        lines.append("=" * 50)

        if self.agent_self:
            health = self.agent_self.get_health_summary()
            lines.append(f"Agent ID: {health['identity']}")
            lines.append(f"State: {health['survival']}")
            lines.append(f"Energy: {health['energy']}%")
            lines.append(f"Risk: {health['risk']}")

        if self.world_model:
            summary = self.world_model.get_world_summary()
            lines.append(f"World Objects: {summary['total_objects']}")

        if self.experience:
            stats = self.experience.get_stats()
            lines.append(f"Experiences: {stats['total_experiences']}")
            lines.append(f"Lessons: {stats['lessons_learned']}")

        lines.append("=" * 50)
        return "\n".join(lines)
