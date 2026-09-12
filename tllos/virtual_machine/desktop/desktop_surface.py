#!/usr/bin/env python3
"""
TLL OS Reality Control Center Desktop

Integrates Agent Live Loop with desktop UI.
"""

import time
from typing import Dict, List, Optional

from .theme.theme import TLLFlatTheme
from .layout.layout_manager import TLLLayoutManager
from ..framebuffer import TLLFramebuffer
from ..text_renderer import TLLTextRenderer
from ..agent.agent_self import TLLAgentSelf
from ..agent.world_model import TLLWorldModel
from ..agent.experience_memory import TLLExperienceMemory
from ..agent.app_runtime import TLLAppRuntime
from ..agent.tool_runtime import TLLToolRuntime
from ..agent.agent_live_loop import TLLAgentLiveLoop


class TLLControlCenterDesktop:
    """TLL OS Reality Control Center."""

    def __init__(self, framebuffer: TLLFramebuffer,
                 agent_self: TLLAgentSelf = None,
                 world_model: TLLWorldModel = None,
                 experience: TLLExperienceMemory = None,
                 app_runtime: TLLAppRuntime = None,
                 tool_runtime: TLLToolRuntime = None,
                 live_loop: TLLAgentLiveLoop = None):
        self.fb = framebuffer
        self.width = framebuffer.width
        self.height = framebuffer.height
        self.text_renderer = TLLTextRenderer(framebuffer)
        self.layout = TLLLayoutManager(self.width, self.height)

        # Runtime bindings
        self.agent_self = agent_self
        self.world_model = world_model
        self.experience = experience
        self.app_runtime = app_runtime
        self.tool_runtime = tool_runtime
        self.live_loop = live_loop

        # State
        self.command_history: List[Dict] = []
        self.frame_count = 0
        self.start_time = time.time()

    def render(self) -> Dict:
        """Render one frame."""
        self.fb.clear(*TLLFlatTheme.TLL_BACKGROUND)
        self.frame_count += 1

        self._render_title_bar()
        self._render_agent_panel()
        self._render_plan_panel()
        self._render_capability_panel()
        self._render_world_panel()
        self._render_command_panel()

        self.fb.commit()
        frame_hash = self.fb.buffer_hash

        return {
            "frame_hash": frame_hash,
            "frame_count": self.frame_count,
            "uptime": time.time() - self.start_time,
            "panels_rendered": 5
        }

    def _render_title_bar(self):
        """Render title bar with TLL OS identity."""
        self.fb.fill_rect(0, 0, self.width, 48, *TLLFlatTheme.TLL_PANEL)

        # TLL OS Boot identity
        self.text_renderer.draw_text(24, 14, "TLL OS",
                                     *TLLFlatTheme.TLL_PRIMARY, size='large')

        # Agent online status
        status = "🤖 tll-agent-0 ONLINE"
        self.text_renderer.draw_text(120, 16, status,
                                     *TLLFlatTheme.TLL_ALIVE, size='small')

        # Uptime
        uptime = int(time.time() - self.start_time)
        self.text_renderer.draw_text(self.width - 80, 16, f"{uptime}s",
                                     *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')

    def _render_agent_panel(self):
        """Render Agent status panel."""
        x = 24
        y = 64
        w = self.width - 48
        h = 100

        self.fb.fill_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(x, y, w, h, *TLLFlatTheme.TLL_PRIMARY)

        self.text_renderer.draw_text(x + 16, y + 6, "🤖 AGENT",
                                     *TLLFlatTheme.TLL_PRIMARY, size='medium')

        if self.live_loop:
            status = self.live_loop.get_status()
            self.text_renderer.draw_text(x + 16, y + 32,
                              f"Goal: {status['goal'] or '等待指令'}",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            self.text_renderer.draw_text(x + 16, y + 50,
                              f"Thinking: {status['thinking']}",
                              *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')
            if status["waiting_approval"]:
                self.text_renderer.draw_text(x + 16, y + 68,
                                  "⏳ WAITING FOR APPROVAL",
                                  *TLLFlatTheme.TLL_WARNING, size='small')

    def _render_plan_panel(self):
        """Render Plan panel."""
        x = 24
        y = 180
        w = self.width - 48
        h = 120

        self.fb.fill_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL_BORDER)

        self.text_renderer.draw_text(x + 16, y + 6, "📋 PLAN",
                                     *TLLFlatTheme.TLL_PRIMARY, size='medium')

        if self.live_loop and self.live_loop.current_plan:
            for i, step in enumerate(self.live_loop.current_plan):
                step_y = y + 32 + i * 16
                done = i < self.live_loop.current_step
                mark = "✓" if done else "○"
                color = TLLFlatTheme.TLL_ALIVE if done else TLLFlatTheme.TLL_TEXT_SECONDARY
                self.text_renderer.draw_text(x + 16, step_y,
                                  f"{mark} {step}",
                                  *color, size='small')

    def _render_capability_panel(self):
        """Render Capability panel."""
        x = 24
        y = 316
        w = (self.width - 48 - 16) // 2
        h = 80

        self.fb.fill_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL_BORDER)

        self.text_renderer.draw_text(x + 16, y + 6, "🛠 CAPABILITY",
                                     *TLLFlatTheme.TLL_PRIMARY, size='medium')

        if self.tool_runtime:
            count = len(self.tool_runtime.tool_handlers)
            self.text_renderer.draw_text(x + 16, y + 32,
                              f"Tools: {count} active",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            self.text_renderer.draw_text(x + 16, y + 50,
                              "File ✓  Code ✓  App ✓",
                              *TLLFlatTheme.TLL_ALIVE, size='small')

    def _render_world_panel(self):
        """Render World panel."""
        x = 24 + (self.width - 48 - 16) // 2 + 16
        y = 316
        w = (self.width - 48 - 16) // 2
        h = 80

        self.fb.fill_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL_BORDER)

        self.text_renderer.draw_text(x + 16, y + 6, "🌍 WORLD",
                                     *TLLFlatTheme.TLL_PRIMARY, size='medium')

        if self.world_model:
            summary = self.world_model.get_world_summary()
            self.text_renderer.draw_text(x + 16, y + 32,
                              f"Objects: {summary['total_objects']}",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')

    def _render_command_panel(self):
        """Render Command panel."""
        x = 24
        y = 412
        w = self.width - 48
        h = 80

        self.fb.fill_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(x, y, w, h, *TLLFlatTheme.TLL_CREATION)

        self.text_renderer.draw_text(x + 16, y + 6, "⌨ COMMAND",
                                     *TLLFlatTheme.TLL_CREATION, size='medium')

        # Last command
        if self.command_history:
            last = self.command_history[-1]
            self.text_renderer.draw_text(x + 16, y + 32,
                              f"> {last['command'][:40]}",
                              *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')
        else:
            self.text_renderer.draw_text(x + 16, y + 32,
                              "> 等待主人指令...",
                              *TLLFlatTheme.TLL_TEXT_MUTED, size='small')

        # Approval button hint
        if self.live_loop and self.live_loop.waiting_approval:
            self.text_renderer.draw_text(x + 16, y + 52,
                              "[批准执行] [拒绝]",
                              *TLLFlatTheme.TLL_WARNING, size='small')

    def submit_command(self, command: str) -> Dict:
        """Submit command to agent live loop."""
        self.command_history.append({
            "command": command,
            "timestamp": time.time(),
            "result": None
        })

        if self.live_loop:
            # Run one cycle
            result = self.live_loop.run_cycle(goal=command)
            self.render()
            return result
        else:
            self.render()
            return {"command": command, "status": "RECEIVED"}

    def approve_execution(self) -> Dict:
        """Approve current execution."""
        if self.live_loop:
            self.live_loop.approve()
            self.render()
            return {"status": "APPROVED", "action": self.live_loop.current_action}
        return {"status": "NO_AGENT"}

    def take_screenshot(self, path: str) -> Dict:
        """Take screenshot."""
        result = self.render()
        try:
            from PIL import Image
            pixels = self.fb.get_pixel_data()
            img = Image.fromarray(pixels, 'RGB')
            img.save(path)
            saved = True
        except Exception:
            saved = False

        return {
            "screenshot": path if saved else "[error]",
            "frame_hash": result["frame_hash"],
            "saved": saved
        }

    def get_status_text(self) -> str:
        """Get status report."""
        lines = [
            "=" * 50,
            "TLL OS CONTROL CENTER",
            "=" * 50,
            f"Agent: tll-agent-0 ONLINE",
        ]

        if self.live_loop:
            status = self.live_loop.get_status()
            lines.append(f"Goal: {status['goal'] or '等待指令'}")
            lines.append(f"Thinking: {status['thinking']}")
            lines.append(f"Plan: {len(status['plan'])} steps")
            lines.append(f"Loop: {status['loop_count']}")

        lines.append(f"Frame: {self.fb.buffer_hash[:16] if self.fb.buffer_hash else '---'}")
        lines.append(f"Uptime: {int(time.time() - self.start_time)}s")
        lines.append("=" * 50)
        return "\n".join(lines)
