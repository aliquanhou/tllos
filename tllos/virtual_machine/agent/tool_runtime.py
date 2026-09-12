#!/usr/bin/env python3
"""
TLL OS Tool Runtime Engine

Real tool execution - connects Tool Registry to actual Runtime.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .tool_registry import TLLToolRegistry
from .virtual_filesystem import TLLVirtualFileSystem
from .process_manager import TLLProcessManager
from .code_runtime import TLLCodeRuntime
from .app_runtime import TLLAppRuntime
from ..window_system import TLLWindowManager, TLLCompositor


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    tool_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class TLLToolRuntime:
    """TLL OS Tool Runtime - real execution engine."""

    def __init__(self, window_manager: TLLWindowManager, compositor: TLLCompositor):
        self.wm = window_manager
        self.compositor = compositor

        # Real subsystem implementations
        self.filesystem = TLLVirtualFileSystem()
        self.process_mgr = TLLProcessManager()
        self.code_runtime = TLLCodeRuntime(self.process_mgr)
        self.app_runtime = TLLAppRuntime(self.wm, self.process_mgr)

        self.execution_history: List[ToolExecutionResult] = []
        self._bind_tools()

    def _bind_tools(self):
        """Bind registered tools to real implementations."""
        self.tool_handlers = {
            "display.create_window": self._create_window,
            "display.draw": self._draw,
            "display.text": self._draw_text,
            "display.screenshot": self._screenshot,
            "storage.read": self._storage_read,
            "storage.write": self._storage_write,
            "storage.list": self._storage_list,
            "process.start": self._process_start,
            "process.stop": self._process_stop,
            "process.list": self._process_list,
            "code.generate": self._code_generate,
            "code.run": self._code_run,
            "app.create": self._app_create,
            "app.launch": self._app_launch,
            "app.close": self._app_close,
        }

    def execute_tool(self, tool_name: str, **kwargs) -> ToolExecutionResult:
        """Execute a tool by name."""
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            result = ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool not found: {tool_name}"
            )
            self.execution_history.append(result)
            return result

        try:
            output = handler(**kwargs)
            result = ToolExecutionResult(
                tool_name=tool_name,
                success=True,
                output=output
            )
        except Exception as e:
            result = ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=str(e)
            )

        self.execution_history.append(result)
        return result

    # Display tools
    def _create_window(self, title: str = "Untitled", x: int = 50, y: int = 50,
                       width: int = 400, height: int = 300) -> Dict:
        """Create a real window via Window Manager."""
        win = self.wm.create_window(title, x, y, width, height)
        self.compositor.composite()
        return {
            "window_id": win.id,
            "title": win.title,
            "x": win.x, "y": win.y,
            "width": win.width, "height": win.height
        }

    def _draw(self, window_id: str = None, action: str = "clear",
              color: List[int] = [40, 50, 65]) -> Dict:
        """Draw on a window."""
        if window_id:
            for w in self.wm.windows:
                if w.id == window_id:
                    if action == "clear":
                        w.clear(*color)
                    elif action == "border":
                        w.draw_border(*color)
                    self.compositor.composite()
                    return {"window_id": window_id, "action": action}
        return {"error": "Window not found"}

    def _draw_text(self, window_id: str = None, text: str = "",
                   x: int = 10, y: int = 10) -> Dict:
        """Draw text on a window (placeholder)."""
        return {"window_id": window_id, "text": text, "action": "draw_text"}

    def _screenshot(self) -> Dict:
        """Trigger screenshot (composite current state)."""
        result = self.compositor.composite()
        return {"frame": result["frame"], "hash": result["hash"]}

    # Storage tools (real)
    def _storage_read(self, path: str) -> Dict:
        """Read file from virtual filesystem."""
        return self.filesystem.read_file(path)

    def _storage_write(self, path: str, content: str = "") -> Dict:
        """Write file to virtual filesystem."""
        return self.filesystem.write_file(path, content)

    def _storage_list(self, dir: str = "/") -> Dict:
        """List virtual directory."""
        return self.filesystem.list_dir(dir)

    # Process tools (real)
    def _process_start(self, name: str) -> Dict:
        """Start real process."""
        return self.process_mgr.start_process(name)

    def _process_stop(self, pid: int) -> Dict:
        """Stop real process."""
        return self.process_mgr.stop_process(pid)

    def _process_list(self) -> Dict:
        """List real processes."""
        return self.process_mgr.list_processes()

    # Code tools (real)
    def _code_generate(self, description: str) -> Dict:
        """Generate code."""
        return self.code_runtime.generate_code(description)

    def _code_run(self, code: str) -> Dict:
        """Run code."""
        result = self.code_runtime.run_code(code)
        return {
            "output": result.output,
            "success": result.success,
            "execution_time_ms": result.execution_time_ms,
            "lines": result.lines_of_code
        }

    # App tools (real)
    def _app_create(self, name: str, type: str = "window") -> Dict:
        """Create application."""
        return self.app_runtime.create_app(name, type)

    def _app_launch(self, app_id: str) -> Dict:
        """Launch application."""
        return self.app_runtime.launch_app(app_id)

    def _app_close(self, app_id: str) -> Dict:
        """Close application."""
        return self.app_runtime.close_app(app_id)

    def get_execution_count(self) -> int:
        return len(self.execution_history)

    def get_execution_history(self) -> List[Dict]:
        return [
            {"tool": r.tool_name, "success": r.success, "timestamp": r.timestamp}
            for r in self.execution_history
        ]
