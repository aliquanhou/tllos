#!/usr/bin/env python3
"""
TLL OS Native Input Boundary

Uses ctypes to call Windows SendInput API.
No pyautogui dependency.
All input must pass through Permission Gate first.
"""

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
SendInput = user32.SendInput

# Input types
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

# Mouse flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000

# Keyboard flags
KEYEVENTF_KEYUP = 0x0002


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


class NativeInputBoundary:
    """Native input boundary - all input must go through this."""

    def __init__(self):
        self._permitted = False

    def grant_permission(self):
        """Permission Gate grants access."""
        self._permitted = True

    def revoke_permission(self):
        """Permission Gate revokes access."""
        self._permitted = False

    def move_mouse(self, x, y):
        """Move mouse - requires permission."""
        if not self._permitted:
            return {"success": False, "error": "PERMISSION_DENIED"}

        # Convert to absolute coordinates (0-65535)
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        abs_x = int(x * 65535 / screen_width)
        abs_y = int(y * 65535 / screen_height)

        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi = MOUSEINPUT(abs_x, abs_y, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, None)

        result = SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
        return {"success": result > 0, "x": x, "y": y}

    def click(self, x, y):
        """Click mouse - requires permission."""
        if not self._permitted:
            return {"success": False, "error": "PERMISSION_DENIED"}

        self.move_mouse(x, y)

        # Mouse down
        inp_down = INPUT()
        inp_down.type = INPUT_MOUSE
        inp_down.union.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, None)
        SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(inp_down))

        # Mouse up
        inp_up = INPUT()
        inp_up.type = INPUT_MOUSE
        inp_up.union.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, None)
        SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(inp_up))

        return {"success": True, "action": "click", "x": x, "y": y}


if __name__ == "__main__":
    boundary = NativeInputBoundary()
    print(f"Permission granted: {boundary._permitted}")
    result = boundary.move_mouse(100, 100)
    print(f"Move without permission: {result}")
    boundary.grant_permission()
    print(f"Permission granted: {boundary._permitted}")
