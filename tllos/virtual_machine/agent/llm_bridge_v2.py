#!/usr/bin/env python3
"""
TLL OS LLM Bridge

Pluggable LLM provider interface.
LLM is a brain plugin, not the OS.
"""

import time
from typing import Dict, List, Optional, Protocol


class TLLLLMProvider(Protocol):
    """LLM provider interface."""

    def think(self, goal: str, context: Dict) -> Dict:
        """Think about a goal."""
        ...

    def plan(self, goal: str, world_state: Dict) -> List[str]:
        """Generate a plan."""
        ...

    def evaluate(self, action: str, context: Dict) -> Dict:
        """Evaluate an action."""
        ...


class TLLMockLLMProvider:
    """Mock LLM provider (default)."""

    def __init__(self):
        self.name = "tll-mock-1.0"

    def think(self, goal: str, context: Dict) -> Dict:
        """Mock thinking."""
        time.sleep(0.05)
        return {
            "thought": f"Analyzing goal: {goal[:30]}",
            "needs": self._analyze_needs(goal),
            "confidence": 0.85
        }

    def plan(self, goal: str, world_state: Dict) -> List[str]:
        """Mock planning."""
        needs = self._analyze_needs(goal)
        plan = [f"创建 {need}" for need in needs]
        plan.append("验证结果")
        return plan

    def evaluate(self, action: str, context: Dict) -> Dict:
        """Mock evaluation."""
        return {
            "action": action,
            "risk": "MEDIUM",
            "approved": True
        }

    def _analyze_needs(self, goal: str) -> List[str]:
        """Analyze what the goal needs."""
        needs = []
        if any(k in goal.lower() for k in ["商城", "mall", "电商", "ecommerce"]):
            needs = ["项目结构", "数据库", "后端API", "前端界面", "测试验证"]
        elif any(k in goal.lower() for k in ["应用", "app", "网站", "website"]):
            needs = ["项目初始化", "核心功能", "UI界面", "部署测试"]
        elif any(k in goal.lower() for k in ["文件", "file"]):
            needs = ["创建文件", "写入内容"]
        else:
            needs = ["分析目标", "制定计划", "执行步骤"]
        return needs

    def chat(self, message: str, context: Dict = None) -> str:
        """Simple chat response."""
        msg = message.lower()
        if any(k in msg for k in ["你好", "hello", "hi", "在吗"]):
            return "你好！我是 TLL OS 智能代理 tll-agent-0。我已就绪，可以帮你创建应用、管理文件、分析任务。请告诉我你想做什么？"
        elif any(k in msg for k in ["你是谁", "什么", "介绍"]):
            return "我是 TLL OS 的第一公民 Agent。我运行在 TLL 自有虚拟机中，有视觉、记忆、能力和证据系统。我的职责是理解你的目标并自主执行。"
        elif any(k in msg for k in ["创建", "做", "写", "build", "create"]):
            needs = self._analyze_needs(message)
            return f"收到你的目标。我分析需要：{', '.join(needs)}。正在制定计划..."
        elif any(k in msg for k in ["谢谢", "感谢", "thanks"]):
            return "不客气！随时为你服务。"
        elif any(k in msg for k in ["停止", "停止", "stop", "退出"]):
            return "好的，已暂停。输入新指令继续。"
        elif any(k in msg for k in ["状态", "status", "情况"]):
            return "我在线。能力：15个工具。世界模型：3个对象。证据记录：正在运行。"
        elif any(k in msg for k in ["帮助", "help", "功能"]):
            return "我可以：创建应用、管理文件、分析任务、制定计划。直接告诉我你的目标即可。"
        else:
            return f"收到: {message[:30]}。我正在理解你的需求，请稍等。"


class TLLLLMBridge:
    """LLM Bridge - connects Agent to LLM providers."""

    def __init__(self, provider: TLLLLMProvider = None):
        self.provider = provider or TLLMockLLMProvider()
        self.provider_name = self.provider.name if hasattr(self.provider, 'name') else "unknown"
        self.call_count = 0

    def think(self, goal: str, context: Dict) -> Dict:
        """Think about a goal."""
        self.call_count += 1
        return self.provider.think(goal, context)

    def plan(self, goal: str, world_state: Dict) -> List[str]:
        """Generate a plan."""
        self.call_count += 1
        return self.provider.plan(goal, world_state)

    def evaluate(self, action: str, context: Dict) -> Dict:
        """Evaluate an action."""
        self.call_count += 1
        return self.provider.evaluate(action, context)

    def chat(self, message: str, context: Dict = None) -> str:
        """Chat with user."""
        self.call_count += 1
        if hasattr(self.provider, 'chat'):
            return self.provider.chat(message, context)
        return f"收到: {message[:30]}"

    def get_status(self) -> Dict:
        """Get LLM bridge status."""
        return {
            "provider": self.provider_name,
            "calls": self.call_count,
            "type": "mock" if "mock" in self.provider_name else "real"
        }
