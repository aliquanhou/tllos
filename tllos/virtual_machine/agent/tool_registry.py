#!/usr/bin/env python3
"""
TLL OS Tool Capability Registry

Agent's capabilities to interact with TLL OS.
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class Tool:
    """TLL OS Tool definition."""
    name: str
    description: str
    category: str
    handler: Optional[Callable] = None
    enabled: bool = True


class TLLToolRegistry:
    """TLL OS Tool Capability Registry."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default TLL OS tools."""
        default_tools = [
            # Display tools
            Tool("display.create_window", "Create a new window", "display"),
            Tool("display.draw", "Draw on window", "display"),
            Tool("display.text", "Render text", "display"),
            Tool("display.screenshot", "Export screenshot", "display"),

            # Storage tools
            Tool("storage.read", "Read file from virtual storage", "storage"),
            Tool("storage.write", "Write file to virtual storage", "storage"),
            Tool("storage.list", "List directory", "storage"),

            # Process tools
            Tool("process.start", "Start a process", "process"),
            Tool("process.stop", "Stop a process", "process"),
            Tool("process.list", "List running processes", "process"),

            # Code generation tools
            Tool("code.generate", "Generate code", "code"),
            Tool("code.run", "Run generated code", "code"),

            # App creation tools
            Tool("app.create", "Create new application", "app"),
            Tool("app.launch", "Launch application", "app"),
            Tool("app.close", "Close application", "app"),
        ]

        for tool in default_tools:
            self.tools[tool.name] = tool

    def register_tool(self, name: str, description: str, category: str,
                      handler: Optional[Callable] = None):
        """Register a new tool."""
        self.tools[name] = Tool(name, description, category, handler)

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self.tools.get(name)

    def list_tools(self, category: Optional[str] = None) -> List[Dict]:
        """List available tools."""
        tools = []
        for name, tool in self.tools.items():
            if category and tool.category != category:
                continue
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "enabled": tool.enabled
            })
        return tools

    def get_capabilities_summary(self) -> Dict:
        """Get capabilities summary for Agent."""
        categories = {}
        for tool in self.tools.values():
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool.name)

        return {
            "total_tools": len(self.tools),
            "categories": list(categories.keys()),
            "tools_by_category": categories
        }
