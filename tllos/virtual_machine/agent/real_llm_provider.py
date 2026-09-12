#!/usr/bin/env python3
"""
TLL OS Real LLM Provider

Connects to real LLM API (Doubao/OpenAI compatible).
Config via config/llm.json
"""

import json
import os
import requests
from typing import Dict, List


class TLLRealLLMProvider:
    """Real LLM provider via HTTP API."""

    def __init__(self, config_path: str = "config/llm.json"):
        self.name = "tll-real-llm"
        self.config_path = config_path
        self.config = self._load_config(config_path)
        # API key from env var (not logged, not in git)
        import os
        self.api_key = os.environ.get("TLL_LLM_API_KEY", self.config.get("api_key", ""))
        self.available = bool(self.api_key)

    def _load_config(self, path: str) -> Dict:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def chat(self, message: str, context: Dict = None) -> str:
        """Send message to real LLM (streaming)."""
        if not self.available:
            return self._fallback(message)

        try:
            url = self.config.get("base_url", "https://api.deepseek.com/v1/chat/completions")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.config.get("model", "deepseek-chat"),
                "messages": [
                    {"role": "system", "content": "你是 TLL OS 的智能代理助手，用中文简洁回答。"},
                    {"role": "user", "content": message}
                ],
                "max_tokens": 500,
                "temperature": 0.7,
                "stream": True
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=30, stream=True)
            if resp.status_code == 200:
                full_reply = ""
                for line in resp.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith("data: "):
                            data_str = line_str[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0].get("delta", {}).get("content", "")
                                if delta:
                                    full_reply += delta
                                    if hasattr(self, 'stream_callback') and self.stream_callback:
                                        self.stream_callback(full_reply)
                            except:
                                pass
                return full_reply if full_reply else "（无回复）"
            return f"API错误: {resp.status_code}"
        except Exception as e:
            return f"连接失败: {str(e)[:50]}"

    def _fallback(self, message: str) -> str:
        """Fallback when no API key configured."""
        msg = message.lower()
        if any(k in msg for k in ["你好", "hello", "hi"]):
            return "你好！我是 TLL OS 智能代理。配置 config/llm.json 中的 API key 可接入真实大模型。"
        elif any(k in msg for k in ["创建", "做"]):
            return f"收到: {message[:30]}。需要配置 API key 才能真正执行创建任务。"
        return f"已收到: {message[:40]}"

    def think(self, goal: str, context: Dict = None) -> Dict:
        return {"thought": self.chat(goal), "confidence": 0.9}

    def plan(self, goal: str, world_state: Dict = None) -> List[str]:
        return ["分析目标", "制定计划", "执行步骤", "验证结果"]

    def evaluate(self, action: str, context: Dict = None) -> Dict:
        return {"risk": "LOW", "approved": True}
