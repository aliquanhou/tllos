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

    def get_status(self) -> Dict:
        """Get LLM bridge status."""
        return {
            "provider": self.provider_name,
            "calls": self.call_count,
            "type": "mock" if "mock" in self.provider_name else "real"
        }
