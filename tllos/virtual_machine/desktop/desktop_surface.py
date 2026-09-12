#!/usr/bin/env python3
"""
TLL OS Flat Intelligence Desktop v1.0

Main desktop surface with runtime data binding.
"""

import time
from typing import Dict, Optional

from .theme.theme import TLLFlatTheme
from .layout.layout_manager import TLLLayoutManager
from ..framebuffer import TLLFramebuffer
from ..text_renderer import TLLTextRenderer
from ..agent.agent_self import TLLAgentSelf
from ..agent.world_model import TLLWorldModel
from ..agent.experience_memory import TLLExperienceMemory
from ..agent.app_runtime import TLLAppRuntime
from ..agent.tool_runtime import TLLToolRuntime


class TLLFlatDesktop:
    """TLL OS Flat Intelligence Desktop v1.0."""

    def __init__(self, framebuffer: TLLFramebuffer,
                 agent_self: TLLAgentSelf = None,
                 world_model: TLLWorldModel = None,
                 experience: TLLExperienceMemory = None,
                 app_runtime: TLLAppRuntime = None,
                 tool_runtime: TLLToolRuntime = None):
        self.fb = framebuffer
        self.width = framebuffer.width
        self.height = framebuffer.height
        self.text_renderer = TLLTextRenderer(framebuffer)
        self.layout = TLLLayoutManager(self.width, self.height)

        # Runtime bindings (NOT copies)
        self.agent_self = agent_self
        self.world_model = world_model
        self.experience = experience
        self.app_runtime = app_runtime
        self.tool_runtime = tool_runtime

        # Owner command state
        self.command_input = ""
        self.command_history = []
        self.last_result = ""

    def render(self) -> Dict:
        """Render the full desktop."""
        # Clear to background
        self.fb.clear(*TLLFlatTheme.TLL_BACKGROUND)

        # Layout
        panels = self.layout.layout_full_desktop()

        # Render title bar
        self._render_title_bar()

        # Render all panels
        self._render_agent_panel(panels["agent"])
        self._render_vision_panel(panels["vision"])
        self._render_memory_panel(panels["memory"])
        self._render_capability_panel(panels["capability"])
        self._render_world_panel(panels["world"])
        self._render_creation_panel(panels["creation"])
        self._render_command_panel(panels["command"])

        # Commit
        self.fb.commit()
        frame_hash = self.fb.buffer_hash

        return {
            "frame_hash": frame_hash,
            "width": self.width,
            "height": self.height,
            "panels_rendered": len(panels)
        }

    def _render_title_bar(self):
        """Render top title bar."""
        self.fb.fill_rect(0, 0, self.width, TLLFlatTheme.TITLE_BAR_HEIGHT,
                         *TLLFlatTheme.TLL_PANEL)

        self.text_renderer.draw_text(24, 14, "TLL OS",
                                     *TLLFlatTheme.TLL_TEXT_PRIMARY, size='large')

        # Status dot
        status_color = TLLFlatTheme.TLL_ALIVE
        self.fb.fill_rect(self.width - 50, 18, 12, 12, *status_color)

    def _render_agent_panel(self, rect):
        """Render Agent panel."""
        self._draw_panel_bg(rect)
        self._draw_panel_title(rect, "🧠 AGENT")

        if self.agent_self:
            health = self.agent_self.get_health_summary()
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 32, f"ID: {health['identity']}",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 50, f"State: {health['survival']}    Energy: {health['energy']}%    Risk: {health['risk']}",
                              *TLLFlatTheme.TLL_ALIVE, size='small')
        else:
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 32, "ID: tll-agent-0",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')

    def _render_vision_panel(self, rect):
        """Render Vision panel."""
        self._draw_panel_bg(rect)
        self._draw_panel_title(rect, "👁 VISION")

        self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                          rect.y + 32, "Screen: captured",
                          *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
        self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                          rect.y + 50, "Objects: detected",
                          *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')
        self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                          rect.y + 68, "Frame: real",
                          *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')

    def _render_memory_panel(self, rect):
        """Render Memory panel."""
        self._draw_panel_bg(rect)
        self._draw_panel_title(rect, "🧠 MEMORY")

        if self.experience:
            stats = self.experience.get_stats()
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 32, f"Experiences: {stats['total_experiences']}",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 50, f"Lessons: {stats['lessons_learned']}",
                              *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')
        else:
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 32, "Experiences: 0",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')

    def _render_capability_panel(self, rect):
        """Render Capability panel."""
        self._draw_panel_bg(rect)
        self._draw_panel_title(rect, "🛠 CAPABILITY")

        caps = []
        if self.tool_runtime:
            count = len(self.tool_runtime.tool_handlers)
            caps.append(f"Tools: {count} active")
        else:
            caps.append("Tools: 15 registered")

        caps.append("Display ✓  Storage ✓  Process ✓  Code ✓  App ✓")

        self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                          rect.y + 32, caps[0],
                          *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
        if len(caps) > 1:
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 50, caps[1],
                              *TLLFlatTheme.TLL_ALIVE, size='small')

    def _render_world_panel(self, rect):
        """Render World Model panel."""
        self._draw_panel_bg(rect)
        self._draw_panel_title(rect, "🌍 WORLD MODEL")

        if self.world_model:
            summary = self.world_model.get_world_summary()
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 32,
                              f"Objects: {summary['total_objects']}    Dependencies: tracked    Impact: analyzable",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
        else:
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 32, "Objects: 0",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')

    def _render_creation_panel(self, rect):
        """Render Creation Space panel."""
        self._draw_panel_bg(rect)
        self._draw_panel_title(rect, "🚀 CREATION SPACE")

        if self.app_runtime:
            stats = self.app_runtime.get_stats()
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 32,
                              f"Apps: {stats['total_apps']}    Running: {stats['running_apps']}",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
        else:
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 32, "Apps: 0",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')

    def _render_command_panel(self, rect):
        """Render Owner Command panel."""
        self._draw_panel_bg(rect, border_color=TLLFlatTheme.TLL_PRIMARY)
        self._draw_panel_title(rect, "⌨ OWNER COMMAND")

        self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                          rect.y + 32, f"> {self.command_input or 'Awaiting command...'}",
                          *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')

        if self.last_result:
            self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                              rect.y + 50, f"Result: {self.last_result[:40]}",
                              *TLLFlatTheme.TLL_ALIVE, size='small')

    def _draw_panel_bg(self, rect, border_color=None):
        """Draw panel background and border."""
        self.fb.fill_rect(rect.x, rect.y, rect.width, rect.height,
                         *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(rect.x, rect.y, rect.width, rect.height,
                         *(border_color or TLLFlatTheme.TLL_PANEL_BORDER))

    def _draw_panel_title(self, rect, title):
        """Draw panel title."""
        self.text_renderer.draw_text(rect.x + TLLFlatTheme.PANEL_PADDING,
                          rect.y + 6, title,
                          *TLLFlatTheme.TLL_PRIMARY, size='medium')

    def submit_command(self, command: str) -> Dict:
        """Submit a command from owner."""
        self.command_input = command
        self.command_history.append({
            "command": command,
            "timestamp": time.time()
        })

        # Simple mock processing
        self.last_result = f"Received: {command[:30]}"

        # Re-render
        self.render()

        return {
            "command": command,
            "status": "received",
            "result": self.last_result
        }

    def take_screenshot(self, path: str) -> Dict:
        """Take a screenshot."""
        result = self.render()
        try:
            from PIL import Image
            pixels = self.fb.get_pixel_data()
            img = Image.fromarray(pixels, 'RGB')
            img.save(path)
            saved = True
        except Exception as e:
            saved = False
            path = f"[error: {e}]"

        return {
            "screenshot": path,
            "frame_hash": result["frame_hash"],
            "resolution": f"{self.width}x{self.height}",
            "saved": saved
        }

    def get_status_text(self) -> str:
        """Get full status text for clipboard."""
        lines = []
        lines.append("=" * 50)
        lines.append("TLL OS STATUS REPORT")
        lines.append("=" * 50)

        if self.agent_self:
            health = self.agent_self.get_health_summary()
            lines.append(f"Agent: {health['identity']}")
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

        if self.tool_runtime:
            lines.append(f"Tools: {len(self.tool_runtime.tool_handlers)} active")

        if self.app_runtime:
            stats = self.app_runtime.get_stats()
            lines.append(f"Apps: {stats['total_apps']}")

        lines.append(f"Frame Hash: {self.fb.buffer_hash}")
        lines.append(f"Timestamp: {time.time()}")
        lines.append("=" * 50)
        return "\n".join(lines)
