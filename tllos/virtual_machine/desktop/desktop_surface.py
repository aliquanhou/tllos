#!/usr/bin/env python3
"""
TLL OS Reality Execution Desktop

Full agent execution loop with input, LLM, approval, evidence.
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
from ..agent.input_manager import TLLInputManager
from ..agent.llm_bridge_v2 import TLLLLMBridge
from ..agent.approval_gate import TLLApprovalGate
from ..agent.evidence_system import TLLEvidenceSystem


class TLLExecutionDesktop:
    """TLL OS Reality Execution Desktop."""

    def __init__(self, framebuffer: TLLFramebuffer,
                 agent_self: TLLAgentSelf = None,
                 world_model: TLLWorldModel = None,
                 experience: TLLExperienceMemory = None,
                 app_runtime: TLLAppRuntime = None,
                 tool_runtime: TLLToolRuntime = None,
                 live_loop: TLLAgentLiveLoop = None,
                 input_manager: TLLInputManager = None,
                 llm_bridge: TLLLLMBridge = None,
                 approval_gate: TLLApprovalGate = None,
                 evidence_system: TLLEvidenceSystem = None):
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
        self.input_manager = input_manager
        self.llm_bridge = llm_bridge
        self.approval_gate = approval_gate
        self.evidence_system = evidence_system

        self.frame_count = 0
        self.start_time = time.time()

    def render(self) -> Dict:
        """Render one frame."""
        self.fb.clear(*TLLFlatTheme.TLL_BACKGROUND)
        self.frame_count += 1

        self._render_title_bar()
        self._render_agent_panel()
        self._render_plan_panel()
        self._render_approval_panel()
        self._render_evidence_panel()
        self._render_command_panel()
        self._render_buttons()

        self.fb.commit()
        frame_hash = self.fb.buffer_hash

        return {
            "frame_hash": frame_hash,
            "frame_count": self.frame_count,
            "uptime": time.time() - self.start_time,
            "panels_rendered": 5
        }

    def _render_title_bar(self):
        """Title bar."""
        self.fb.fill_rect(0, 0, self.width, 48, *TLLFlatTheme.TLL_PANEL)
        self.text_renderer.draw_text(24, 14, "TLL OS 智能代理",
                                     *TLLFlatTheme.TLL_PRIMARY, size='large')
        self.text_renderer.draw_text(200, 16, "系统在线",
                                     *TLLFlatTheme.TLL_ALIVE, size='small')
        uptime = int(time.time() - self.start_time)
        self.text_renderer.draw_text(self.width - 80, 16, f"{uptime}s",
                                     *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')

    def _render_agent_panel(self):
        """Agent panel."""
        x, y, w, h = 24, 64, self.width - 48, 90
        self.fb.fill_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(x, y, w, h, *TLLFlatTheme.TLL_PRIMARY)
        self.text_renderer.draw_text(x + 16, y + 6, "智能核心",
                                     *TLLFlatTheme.TLL_PRIMARY, size='medium')

        if self.live_loop:
            status = self.live_loop.get_status()
            self.text_renderer.draw_text(x + 16, y + 32,
                              f"当前目标: {status['goal'] or '等待指令'}",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            self.text_renderer.draw_text(x + 16, y + 50,
                              f"思考状态: {status['thinking']}",
                              *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')

    def _render_plan_panel(self):
        """Plan panel."""
        x, y, w, h = 24, 170, self.width - 48, 110
        self.fb.fill_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL_BORDER)
        self.text_renderer.draw_text(x + 16, y + 6, "任务规划",
                                     *TLLFlatTheme.TLL_PRIMARY, size='medium')

        if self.live_loop and self.live_loop.current_plan:
            for i, step in enumerate(self.live_loop.current_plan[:4]):
                sy = y + 32 + i * 16
                done = i < self.live_loop.current_step
                mark = "✓" if done else "○"
                color = TLLFlatTheme.TLL_ALIVE if done else TLLFlatTheme.TLL_TEXT_SECONDARY
                self.text_renderer.draw_text(x + 16, sy,
                                  f"{mark} {step}", *color, size='small')

    def _render_approval_panel(self):
        """Approval gate panel."""
        x = 24
        y = 296
        w = (self.width - 48 - 16) // 2
        h = 80
        self.fb.fill_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(x, y, w, h, *TLLFlatTheme.TLL_WARNING)
        self.text_renderer.draw_text(x + 16, y + 6, "执行权限",
                                     *TLLFlatTheme.TLL_WARNING, size='medium')

        if self.approval_gate and self.approval_gate.has_pending():
            req = self.approval_gate.get_pending()[0]
            self.text_renderer.draw_text(x + 16, y + 32,
                              f"等待: {req.action[:20]}",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            self.text_renderer.draw_text(x + 16, y + 50,
                              f"风险: {req.risk_level}",
                              *TLLFlatTheme.TLL_WARNING, size='small')
        else:
            self.text_renderer.draw_text(x + 16, y + 32,
                              "无待处理请求",
                              *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')

    def _render_evidence_panel(self):
        """Evidence panel."""
        x = 24 + (self.width - 48 - 16) // 2 + 16
        y = 296
        w = (self.width - 48 - 16) // 2
        h = 80
        self.fb.fill_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL_BORDER)
        self.text_renderer.draw_text(x + 16, y + 6, "证据记录",
                                     *TLLFlatTheme.TLL_PRIMARY, size='medium')

        if self.evidence_system:
            stats = self.evidence_system.get_stats()
            self.text_renderer.draw_text(x + 16, y + 32,
                              f"记录数: {stats['total_records']}",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
            self.text_renderer.draw_text(x + 16, y + 50,
                              f"已批准: {stats['approved_count']}",
                              *TLLFlatTheme.TLL_ALIVE, size='small')

    def _render_command_panel(self):
        """Command panel."""
        x, y, w, h = 24, 392, self.width - 48, 70
        self.fb.fill_rect(x, y, w, h, *TLLFlatTheme.TLL_PANEL)
        self.fb.draw_rect(x, y, w, h, *TLLFlatTheme.TLL_CREATION)
        self.text_renderer.draw_text(x + 16, y + 6, "主人指令",
                                     *TLLFlatTheme.TLL_CREATION, size='medium')

        # Show live input buffer from window host
        input_text = ""
        if hasattr(self, '_window_input') and self._window_input:
            input_text = self._window_input

        if input_text:
            self.text_renderer.draw_text(x + 16, y + 32,
                              f"> {input_text}",
                              *TLLFlatTheme.TLL_TEXT_PRIMARY, size='small')
        elif self.input_manager and self.input_manager.command_history:
            last = self.input_manager.command_history[-1]
            self.text_renderer.draw_text(x + 16, y + 32,
                              f"> {last.text[:40]}",
                              *TLLFlatTheme.TLL_TEXT_SECONDARY, size='small')
        else:
            self.text_renderer.draw_text(x + 16, y + 32,
                              "> 等待主人指令...",
                              *TLLFlatTheme.TLL_TEXT_MUTED, size='small')

    def _render_buttons(self):
        """Control buttons at bottom."""
        btn_y = 478
        btn_h = 30
        btn_w = 100
        gap = 12
        start_x = 24

        buttons = [
            ("启动", TLLFlatTheme.TLL_ALIVE),
            ("暂停", TLLFlatTheme.TLL_WARNING),
            ("批准", TLLFlatTheme.TLL_PRIMARY),
            ("停止", TLLFlatTheme.TLL_DANGER),
        ]

        self.buttons = []  # Store button rects for click detection

        for i, (label, color) in enumerate(buttons):
            bx = start_x + i * (btn_w + gap)
            self.fb.fill_rect(bx, btn_y, btn_w, btn_h, *color)
            self.fb.draw_rect(bx, btn_y, btn_w, btn_h, 255, 255, 255)
            # Draw button text centered
            text_x = bx + btn_w // 2 - len(label) * 8
            self.text_renderer.draw_text(text_x, btn_y + 8, label,
                                         5, 8, 18, size='small')
            self.buttons.append((label, bx, btn_y, btn_w, btn_h))

    def submit_command(self, command: str) -> Dict:
        """Submit command through full pipeline."""
        # 1. Input Manager
        if self.input_manager:
            cmd = self.input_manager.submit(command)
        else:
            cmd = type('obj', (object,), {'text': command})()

        # 2. Agent Live Loop
        if self.live_loop:
            result = self.live_loop.run_cycle(goal=command)

            # 3. Record evidence
            if self.evidence_system:
                self.evidence_system.record(
                    action=result.get("last_result", "command"),
                    reason=f"Owner command: {command[:30]}",
                    risk_level="LOW",
                    approved=True,
                    result="SUCCESS"
                )

            self.render()
            return result
        else:
            self.render()
            return {"command": command, "status": "RECEIVED"}

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

        return {"screenshot": path if saved else "[error]",
                "frame_hash": result["frame_hash"], "saved": saved}

    def get_status_text(self) -> str:
        """Get status report."""
        lines = ["=" * 50, "TLL OS EXECUTION STATUS", "=" * 50]

        if self.llm_bridge:
            llm_status = self.llm_bridge.get_status()
            lines.append(f"LLM: {llm_status['provider']} ({llm_status['calls']} calls)")

        if self.approval_gate:
            lines.append(f"Approval: {self.approval_gate.get_status()['pending']} pending")

        if self.evidence_system:
            lines.append(f"Evidence: {self.evidence_system.get_stats()['total_records']} records")

        lines.append(f"Frame: {self.fb.buffer_hash[:16] if self.fb.buffer_hash else '---'}")
        lines.append("=" * 50)
        return "\n".join(lines)
