#!/usr/bin/env python3
"""
TLL OS Flat Intelligence Desktop Reality UI

Real-time interactive desktop with live agent state.
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


class TLLRealityDesktop:
    """TLL OS Flat Intelligence Desktop Reality UI."""

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

        # Runtime bindings
        self.agent_self = agent_self
        self.world_model = world_model
        self.experience = experience
        self.app_runtime = app_runtime
        self.tool_runtime = tool_runtime

        # Real-time state
        self.current_goal = ""
        self.current_thinking = ""
        self.current_plan: List[str] = []
        self.current_action = ""
        self.vision_objects: List[str] = []
        self.command_history: List[Dict] = []
        self.last_result = ""
        self.frame_count = 0
        self.start_time = time.time()

    def render(self) -> Dict:
        """Render one frame."""
        self.fb.clear(*TLLFlatTheme.TLL_BACKGROUND)
        self.frame_count += 1

        panels = self._layout_panels()

        # Title bar
        self._render_title_bar()

        # All panels
        self._render_vision_panel(panels["vision"])
        self._render_agent_panel(panels["agent"])
        self._render_memory_panel(panels["memory"])
        self._render_capability_panel(panels["capability"])
        self._render_world_panel(panels["world"])
        self._render_command_panel(panels["command"])

        self.fb.commit()
        frame_hash = self.fb.buffer_hash

        return {
            "frame_hash": frame_hash,
            "frame_count": self.frame_count,
            "uptime": time.time() - self.start_time,
            "panels_rendered": 6
        }

    def _layout_panels(self) -> Dict:
        """Layout all panels."""
        margin = TLLFlatTheme.MARGIN
        spacing = TLLFlatTheme.PANEL_SPACING
        title_h = TLLFlatTheme.TITLE_BAR_HEIGHT
        col_w = (self.width - 2 * margin - spacing) // 2

        # Vision (left, large)
        vision = self._panel(margin, title_h + margin, col_w, 200, "VISION")

        # Agent Core (right, large)
        agent_x = margin + col_w + spacing
        agent = self._panel(agent_x, title_h + margin, col_w, 200, "AGENT CORE")

        # Memory (left)
        mem_y = vision.y + vision.height + spacing
        memory = self._panel(margin, mem_y, col_w, 120, "MEMORY")

        # Capability (right)
        cap = self._panel(agent_x, mem_y, col_w, 120, "CAPABILITY")

        # World Model (full width)
        world_y = mem_y + 120 + spacing
        world = self._panel(margin, world_y, self.width - 2 * margin, 60, "WORLD MODEL")

        # Command (full width)
        cmd_y = world_y + 60 + spacing
        command = self._panel(margin, cmd_y, self.width - 2 * margin, 70, "COMMAND")

        return {
            "vision": vision, "agent": agent,
            "memory": memory, "capability": cap,
            "world": world, "command": command
        }

    def _panel(self, x, y, w, h, title=""):
        """Helper to create panel rect."""
        from .layout.layout_manager import PanelRect
        return PanelRect(x, y, w, h, title)

    def _render_title_bar(self):
        """Render title bar."""
        self.fb.fill_rect(0, 0, self.width, 48, *TLLFlatTheme.TLL_PANEL)

        self.text_renderer.draw_text(24, 14, "TLL OS",
                                     *TLLFlatTheme.TLL_TEXT_PRIMARY, size='large')

        # Status
        status = "ONLINE" if self.agent_self else "READY"
        self.text_renderer.draw_text(120, 16, f"● {status}",
                                     *TLLFlatTheme.TLL_ALIVE, size='small')

        # Uptime
        uptime = int(time.time() - self.start_time)
        self.text_renderer.draw_text(self.width - 100, 16, f"{uptime}s",
                                     *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')

    def _render_vision_panel(self, rect):
        """Render Vision panel."""
        self._panel_bg(rect)
        self._panel_title(rect, "👁 VISION")

        # Current observation
        y = rect.y + 32
        self.text_renderer.draw_text(rect.x + 16, y,
                          "当前观察: Desktop",
                          *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
        y += 18

        # Objects
        if self.vision_objects:
            for obj in self.vision_objects[:3]:
                self.text_renderer.draw_text(rect.x + 24, y,
                                  f"├─ {obj}",
                                  *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')
                y += 16
        else:
            self.text_renderer.draw_text(rect.x + 24, y,
                              "├─ 等待观察...",
                              *TLLFlatTheme.TLL_TEXT_MUTED, size='small')
            y += 16

        # Frame hash
        self.text_renderer.draw_text(rect.x + 16, rect.y + rect.height - 20,
                          f"Frame: {self.fb.buffer_hash[:12] if self.fb.buffer_hash else '---'}",
                          *TLLFlatTheme.TLL_TEXT_MUTED, size='small')

    def _render_agent_panel(self, rect):
        """Render Agent Core panel."""
        self._panel_bg(rect, border=TLLFlatTheme.TLL_PRIMARY)
        self._panel_title(rect, "🧠 AGENT CORE")

        y = rect.y + 32

        # Identity
        if self.agent_self:
            health = self.agent_self.get_health_summary()
            self.text_renderer.draw_text(rect.x + 16, y,
                              f"ID: {health['identity']}",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            y += 18
            self.text_renderer.draw_text(rect.x + 16, y,
                              f"State: {health['survival']}  Energy: {health['energy']}%",
                              *TLLFlatTheme.TLL_ALIVE, size='small')
        else:
            self.text_renderer.draw_text(rect.x + 16, y,
                              "ID: tll-agent-0",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            y += 18

        y += 8

        # Goal
        self.text_renderer.draw_text(rect.x + 16, y,
                          f"目标: {self.current_goal or '等待指令'}",
                          *TLLFlatTheme.TLL_PRIMARY, size='small')
        y += 18

        # Thinking
        self.text_renderer.draw_text(rect.x + 16, y,
                          f"思考: {self.current_thinking or '观察中'}",
                          *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')
        y += 18

        # Plan
        if self.current_plan:
            self.text_renderer.draw_text(rect.x + 16, y,
                              "计划:",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            for i, step in enumerate(self.current_plan[:3]):
                y += 16
                self.text_renderer.draw_text(rect.x + 24, y,
                                  f"{i+1}. {step[:30]}",
                                  *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')

    def _render_memory_panel(self, rect):
        """Render Memory panel."""
        self._panel_bg(rect)
        self._panel_title(rect, "🧠 MEMORY")

        y = rect.y + 32
        if self.experience:
            stats = self.experience.get_stats()
            self.text_renderer.draw_text(rect.x + 16, y,
                              f"经验: {stats['total_experiences']} 条",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            y += 18
            self.text_renderer.draw_text(rect.x + 16, y,
                              f"教训: {stats['lessons_learned']} 条",
                              *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')
        else:
            self.text_renderer.draw_text(rect.x + 16, y,
                              "经验: 0 条",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')

    def _render_capability_panel(self, rect):
        """Render Capability panel."""
        self._panel_bg(rect)
        self._panel_title(rect, "🛠 CAPABILITY")

        y = rect.y + 32
        if self.tool_runtime:
            count = len(self.tool_runtime.tool_handlers)
            self.text_renderer.draw_text(rect.x + 16, y,
                              f"能力: {count} 个",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            y += 18
            self.text_renderer.draw_text(rect.x + 16, y,
                              "✓ 文件 ✓ 进程 ✓ 代码 ✓ 应用",
                              *TLLFlatTheme.TLL_ALIVE, size='small')
        else:
            self.text_renderer.draw_text(rect.x + 16, y,
                              "能力: 15 个",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')

    def _render_world_panel(self, rect):
        """Render World Model panel."""
        self._panel_bg(rect)
        self._panel_title(rect, "🌍 WORLD MODEL")

        if self.world_model:
            summary = self.world_model.get_world_summary()
            self.text_renderer.draw_text(rect.x + 16, rect.y + 32,
                              f"Objects: {summary['total_objects']}  →  DB → Backend → App → User",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
        else:
            self.text_renderer.draw_text(rect.x + 16, rect.y + 32,
                              "Objects: 0",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')

    def _render_command_panel(self, rect):
        """Render Command panel."""
        self._panel_bg(rect, border=TLLFlatTheme.TLL_CREATION)
        self._panel_title(rect, "⌨ COMMAND")

        self.text_renderer.draw_text(rect.x + 16, rect.y + 32,
                          f"> {self.last_result or '等待主人指令...'}",
                          *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')

    def _panel_bg(self, rect, border=None):
        """Draw panel background."""
        self.fb.fill_rect(rect.x, rect.y, rect.width, rect.height,
                         *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(rect.x, rect.y, rect.width, rect.height,
                         *(border or TLLFlatTheme.TLL_PANEL_BORDER))

    def _panel_title(self, rect, title):
        """Draw panel title."""
        self.text_renderer.draw_text(rect.x + 16, rect.y + 6, title,
                                     *TLLFlatTheme.TLL_PRIMARY, size='medium')

    def submit_command(self, command: str) -> Dict:
        """Process owner command through agent reasoning loop."""
        self.command_history.append({
            "command": command,
            "timestamp": time.time(),
            "result": None
        })

        # Simulate agent reasoning
        self.current_goal = command
        self.current_thinking = "分析目标中..."
        self.render()

        # Reasoning steps (mock, but real structure)
        time.sleep(0.1)  # Simulate thinking
        self.current_thinking = "理解需求: 需要创建应用"
        self.render()

        time.sleep(0.1)
        self.current_thinking = "规划步骤: 分解为多个子任务"
        self.current_plan = [
            "分析目标",
            "创建基础结构",
            "生成核心功能",
            "验证结果"
        ]
        self.render()

        time.sleep(0.1)
        self.last_result = f"已接收: {command[:40]}"
        self.current_thinking = "等待执行批准"
        self.render()

        # Record experience
        if self.experience:
            self.experience.record_experience(
                action=f"command_{len(self.command_history)}",
                evidence="command_received",
                world_before={},
                world_after={"goal": command},
                result="RECEIVED",
                lesson=f"Received command: {command[:20]}",
                risk_level="LOW"
            )

        return {
            "command": command,
            "goal": self.current_goal,
            "plan": self.current_plan,
            "status": "RECEIVED"
        }

    def take_screenshot(self, path: str) -> Dict:
        """Take screenshot."""
        result = self.render()
        try:
            from PIL import Image
            pixels = self.fb.get_pixel_data()
            img = Image.fromarray(pixels, 'RGB')
            img.save(path)
            saved = True
        except Exception as e:
            saved = False

        return {
            "screenshot": path if saved else f"[error]",
            "frame_hash": result["frame_hash"],
            "resolution": f"{self.width}x{self.height}",
            "saved": saved
        }

    def get_status_text(self) -> str:
        """Get status report for clipboard."""
        lines = [
            "=" * 50,
            "TLL OS REAL-TIME STATUS",
            "=" * 50,
            f"Agent: {self.agent_self.get_self_state()['identity'] if self.agent_self else 'tll-agent-0'}",
            f"Goal: {self.current_goal or '等待指令'}",
            f"Thinking: {self.current_thinking or '观察中'}",
            f"Plan: {len(self.current_plan)} steps",
            f"Frame: {self.fb.buffer_hash[:16] if self.fb.buffer_hash else '---'}",
            f"Uptime: {int(time.time() - self.start_time)}s",
            "=" * 50
        ]
        return "\n".join(lines)
