#!/usr/bin/env python3
"""
TLL OS Input Manager

Handles owner input: keyboard events, command queue, history.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TLLCommand:
    """Owner command."""
    id: str
    text: str
    timestamp: float
    owner: str = "human"
    status: str = "QUEUED"
    result: Optional[Dict] = None


class TLLInputManager:
    """Manages owner input."""

    def __init__(self):
        self.command_queue: List[TLLCommand] = []
        self.command_history: List[TLLCommand] = []
        self.current_input = ""
        self.owner = "human"
        self._cmd_counter = 0

    def submit(self, command_text: str) -> TLLCommand:
        """Submit a command from owner."""
        self._cmd_counter += 1
        cmd = TLLCommand(
            id=f"cmd_{self._cmd_counter:04d}",
            text=command_text,
            timestamp=time.time(),
            owner=self.owner
        )
        self.command_queue.append(cmd)
        self.command_history.append(cmd)
        return cmd

    def get_next_command(self) -> Optional[TLLCommand]:
        """Get next pending command."""
        if self.command_queue:
            return self.command_queue.pop(0)
        return None

    def has_pending(self) -> bool:
        """Check if there are pending commands."""
        return len(self.command_queue) > 0

    def get_history(self, limit: int = 10) -> List[TLLCommand]:
        """Get command history."""
        return self.command_history[-limit:]

    def get_status(self) -> Dict:
        """Get input manager status."""
        return {
            "pending": len(self.command_queue),
            "history_count": len(self.command_history),
            "owner": self.owner
        }
