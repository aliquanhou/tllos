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
from ..agent.agent_registry import TLLAgentRegistry


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
                 evidence_system: TLLEvidenceSystem = None,
                 agent_registry: TLLAgentRegistry = None):
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
        self.agent_registry = agent_registry

        self.frame_count = 0
        self.start_time = time.time()
        self.event_log = []  # [(timestamp, message)]
        self.chat_history = []  # [("user"/"agent", text)]

    def log_event(self, msg: str):
        """Log an event to the visible event stream."""
        ts = time.strftime("%H:%M:%S")
        self.event_log.append((ts, msg))
        if len(self.event_log) > 8:
            self.event_log = self.event_log[-8:]

    def add_chat(self, role: str, text: str):
        """Add a chat message to history."""
        self.chat_history.append((role, text))
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]

    def render(self) -> Dict:
        """Render TLL Agent Reality Console."""
        # TLL Flat Theme colors
        bg = (5, 8, 18)       # #050812
        panel = (16, 24, 39)   # #101827
        primary = (0, 229, 255)  # #00E5FF
        alive = (0, 255, 136)    # #00FF88
        warn = (255, 204, 0)     # #FFCC00
        danger = (255, 51, 68)   # #FF3344
        creation = (255, 209, 102)  # #FFD166
        text_pri = (230, 230, 230)
        text_sec = (140, 140, 140)
        text_mute = (80, 80, 80)

        self.fb.clear(*bg)
        self.frame_count += 1

        # === Top bar ===
        self.fb.fill_rect(0, 0, self.width, 48, *panel)
        self.fb.draw_rect(0, 47, self.width, 1, *primary)
        self.text_renderer.draw_text(20, 14, "TLL OS", *primary, size='large')
        self.text_renderer.draw_text(130, 16, "智能代理 · 在线", *alive, size='medium')

        # === Left sidebar (200px) ===
        sw = 200
        sx = 0
        sy = 48

        # Agent State
        ay = sy + 12
        self.fb.fill_rect(sx + 10, ay, sw - 20, 100, *panel)
        self.fb.draw_rect(sx + 10, ay, sw - 20, 100, *alive)
        self.text_renderer.draw_text(sx + 20, ay + 8, "Agent", *alive, size='medium')
        if self.agent_self:
            health = self.agent_self.get_health_summary()
            self.text_renderer.draw_text(sx + 20, ay + 34, "状态: 在线", *alive, size='small')
            self.text_renderer.draw_text(sx + 20, ay + 54, f"能量: {health.get('energy', 0)}%", *text_pri, size='small')
            self.text_renderer.draw_text(sx + 20, ay + 74, "LLM: DeepSeek", *text_sec, size='small')

        # Agent Store
        sy2 = ay + 116
        self.fb.fill_rect(sx + 10, sy2, sw - 20, 80, *panel)
        self.fb.draw_rect(sx + 10, sy2, sw - 20, 80, *primary)
        self.text_renderer.draw_text(sx + 20, sy2 + 8, "已安装", *primary, size='medium')
        if self.agent_registry:
            agents = self.agent_registry.list_agents()
            self.text_renderer.draw_text(sx + 20, sy2 + 36, f"Agent: {len(agents)}", *text_pri, size='small')
            for i, ag in enumerate(agents[:2]):
                self.text_renderer.draw_text(sx + 20, sy2 + 56 + i * 16,
                    f"● {ag['name'][:12]}", *text_sec, size='small')

        # === Right: Chat area ===
        rx = sw + 12
        rw = self.width - sw - 24
        ry = 56
        rh = self.height - ry - 70

        # Chat background
        self.fb.fill_rect(rx, ry, rw, rh, *panel)
        self.fb.draw_rect(rx, ry, rw, rh, *primary)

        self.text_renderer.draw_text(rx + 20, ry + 12, "对话", *primary, size='medium')

        # Chat messages - larger font, wrap lines
        cy = ry + 44
        line_width = 70  # chars per line
        if self.chat_history:
            for role, text in self.chat_history[-6:]:
                prefix = "我: " if role == "user" else "TLL: "
                color = alive if role == "user" else text_pri
                # Split text into lines
                full = prefix + text
                while full:
                    line = full[:line_width]
                    self.text_renderer.draw_text(rx + 20, cy, line, *color, size='medium')
                    cy += 26
                    full = full[line_width:]
                cy += 6  # gap between messages
        else:
            self.text_renderer.draw_text(rx + 20, cy, "你好！我是 TLL OS 智能代理", *text_sec, size='medium')
            cy += 32
            self.text_renderer.draw_text(rx + 20, cy, "在下方输入框和我对话", *text_mute, size='small')
            cy += 32

        # === Bottom: Input bar ===
        iy = self.height - 56
        ih = 44
        self.fb.fill_rect(rx, iy, rw, ih, 30, 40, 60)
        self.fb.draw_rect(rx, iy, rw, ih, *primary)

        input_text = ""
        if hasattr(self, '_window_input') and self._window_input:
            input_text = self._window_input

        if input_text:
            self.text_renderer.draw_text(rx + 16, iy + 12, input_text, *text_pri, size='medium')
        else:
            self.text_renderer.draw_text(rx + 16, iy + 12, "输入消息...", *text_mute, size='medium')

        # Send button
        btn_x = rx + rw - 56
        self.fb.fill_rect(btn_x, iy + 4, 48, 36, *alive)
        self.fb.draw_rect(btn_x, iy + 4, 48, 36, 0, 150, 80)
        self.text_renderer.draw_text(btn_x + 10, iy + 12, "发送", 5, 8, 18, size='medium')

        self.buttons = [("send", btn_x, iy + 4, 48, 36)]

        self.fb.commit()
        frame_hash = self.fb.buffer_hash

        return {
            "frame_hash": frame_hash,
            "frame_count": self.frame_count,
            "uptime": time.time() - self.start_time,
            "panels_rendered": 4
        }

    def _render_sidebar(self):
        """Left sidebar like ChatGPT."""
        sw = 240  # sidebar width
        # Sidebar background
        self.fb.fill_rect(0, 0, sw, self.height, 13, 13, 13)  # #0D0D0D

        # New chat button
        self.fb.fill_rect(12, 12, sw - 24, 36, 32, 33, 35)
        self.fb.draw_rect(12, 12, sw - 24, 36, 64, 65, 70)
        self.text_renderer.draw_text(24, 22, "+ 新对话", 255, 255, 255, size='small')

        # Section: 今天
        self.text_renderer.draw_text(16, 64, "今天", 100, 100, 100, size='small')

        # Chat history items
        items = [
            "TLL OS 初始化",
            "创建商城系统",
            "Agent 配置",
        ]
        for i, item in enumerate(items):
            y = 84 + i * 28
            self.fb.fill_rect(8, y, sw - 16, 24, 32, 33, 35)
            self.text_renderer.draw_text(20, y + 5, item, 200, 200, 200, size='small')

        # Section: 之前
        self.text_renderer.draw_text(16, 180, "之前", 100, 100, 100, size='small')

        prev_items = ["系统配置", "工具链"]
        for i, item in enumerate(prev_items):
            y = 200 + i * 28
            self.text_renderer.draw_text(20, y + 5, item, 150, 150, 150, size='small')

        # Bottom: user info
        self.fb.fill_rect(0, self.height - 48, sw, 48, 25, 25, 25)
        self.text_renderer.draw_text(16, self.height - 36, "tll-agent-0", 255, 255, 255, size='small')
        self.text_renderer.draw_text(16, self.height - 18, "在线", 0, 200, 136, size='small')

    def _render_chat_area(self):
        """Main chat area."""
        ox = 240  # offset x (sidebar width)
        cw = self.width - ox  # content width

        # Top bar
        self.fb.fill_rect(ox, 0, cw, 48, 25, 25, 25)
        self.text_renderer.draw_text(ox + 20, 16, "TLL OS 智能代理", 255, 255, 255, size='medium')

        # Chat messages area
        msg_y = 70

        # Get agent status
        goal_text = "等待指令"
        thinking_text = "空闲"
        if self.live_loop:
            status = self.live_loop.get_status()
            goal_text = status.get('goal') or "等待指令"
            thinking_text = status.get('thinking') or "空闲"

        # User message (goal)
        user_msg = f"目标: {goal_text}"
        uw = len(user_msg) * 8 + 32
        self.fb.fill_rect(ox + 400, msg_y, uw, 32, 42, 43, 50)  # user bubble
        self.text_renderer.draw_text(ox + 416, msg_y + 8, user_msg, 255, 255, 255, size='small')

        # Agent response
        msg_y2 = msg_y + 50
        agent_msg1 = f"思考: {thinking_text}"
        aw1 = len(agent_msg1) * 8 + 32
        self.fb.fill_rect(ox + 20, msg_y2, aw1, 32, 33, 33, 33)  # agent bubble
        self.text_renderer.draw_text(ox + 36, msg_y2 + 8, agent_msg1, 220, 220, 220, size='small')

        # Plan status
        if self.live_loop and self.live_loop.current_plan:
            msg_y3 = msg_y2 + 50
            self.text_renderer.draw_text(ox + 20, msg_y3, "任务计划:", 150, 200, 255, size='small')
            for i, step in enumerate(self.live_loop.current_plan[:4]):
                sy = msg_y3 + 20 + i * 18
                done = i < self.live_loop.current_step
                mark = "✓" if done else "○"
                color = (0, 200, 136) if done else (150, 150, 150)
                self.text_renderer.draw_text(ox + 36, sy, f"{mark} {step}", *color, size='small')

        # Evidence status
        if self.evidence_system:
            stats = self.evidence_system.get_stats()
            ey = self.height - 120
            self.text_renderer.draw_text(ox + 20, ey,
                f"证据记录: {stats['total_records']} | 已批准: {stats['approved_count']}",
                100, 100, 100, size='small')

    def _render_input_bar(self):
        """Bottom input bar like ChatGPT."""
        ox = 240
        bar_y = self.height - 60
        bar_h = 40
        bar_w = self.width - ox - 40

        # Input box
        self.fb.fill_rect(ox + 20, bar_y, bar_w, bar_h, 47, 47, 47)
        self.fb.draw_rect(ox + 20, bar_y, bar_w, bar_h, 64, 65, 70)

        # Input text
        input_text = ""
        if hasattr(self, '_window_input') and self._window_input:
            input_text = self._window_input

        if input_text:
            self.text_renderer.draw_text(ox + 36, bar_y + 12, input_text, 255, 255, 255, size='small')
        else:
            self.text_renderer.draw_text(ox + 36, bar_y + 12, "输入你的指令...", 120, 120, 120, size='small')

        # Send button (right side)
        btn_x = ox + 20 + bar_w - 40
        self.fb.fill_rect(btn_x, bar_y + 4, 32, 32, 16, 163, 127)  # ChatGPT green
        self.text_renderer.draw_text(btn_x + 8, bar_y + 12, "↑", 255, 255, 255, size='small')

        # Store clickable areas
        self.buttons = []
        self.buttons.append(("send", btn_x, bar_y + 4, 32, 32))

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
