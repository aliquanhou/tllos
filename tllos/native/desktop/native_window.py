#!/usr/bin/env python3
"""
TLL OS Native Window Placement

Uses ctypes to call Windows user32.dll.
No PySide6 dependency.
"""

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
SetWindowPos = user32.SetWindowPos
MoveWindow = user32.MoveWindow
FindWindowW = user32.FindWindowW

SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010


def move_window_to_monitor(hwnd, monitor_info):
    """Move window to specified monitor."""
    x = monitor_info.get("x", 0)
    y = monitor_info.get("y", 0)
    width = monitor_info.get("width", 1920)
    height = monitor_info.get("height", 1080)

    result = MoveWindow(hwnd, x, y, width, height, True)
    return result != 0


def get_foreground_window():
    """Get current foreground window handle."""
    return user32.GetForegroundWindow()


def find_window(class_name=None, window_name=None):
    """Find window by class or title."""
    return FindWindowW(class_name, window_name)


if __name__ == "__main__":
    fg = get_foreground_window()
    print(f"Foreground window: {fg}")
