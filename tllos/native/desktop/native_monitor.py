#!/usr/bin/env python3
"""
TLL OS Native Monitor Layer

Uses ctypes to call Windows user32.dll directly.
No PySide6 dependency.
No Qt dependency.
"""

import ctypes
import json
from ctypes import wintypes
from pathlib import Path


# Windows API types
user32 = ctypes.windll.user32
EnumDisplayMonitors = user32.EnumDisplayMonitors
GetMonitorInfoW = user32.GetMonitorInfoW

# Monitor info flags
MONITORINFOF_PRIMARY = 0x00000001


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


# Callback type: BOOL CALLBACK MonitorEnumProc(HMONITOR, HDC, LPRECT, LPARAM)
MONITORENUMPROC = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HMONITOR,
    wintypes.HDC,
    ctypes.POINTER(wintypes.RECT),
    wintypes.LPARAM
)

_monitors = []


def _enum_callback(hMonitor, hdc, lprcMonitor, lParam):
    """Callback for EnumDisplayMonitors."""
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    GetMonitorInfoW(hMonitor, ctypes.byref(mi))

    is_primary = (mi.dwFlags & MONITORINFOF_PRIMARY) != 0

    monitor = {
        "handle": hMonitor,
        "id": len(_monitors) + 1,
        "primary": is_primary,
        "x": mi.rcMonitor.left,
        "y": mi.rcMonitor.top,
        "width": mi.rcMonitor.right - mi.rcMonitor.left,
        "height": mi.rcMonitor.bottom - mi.rcMonitor.top,
        "work_x": mi.rcWork.left,
        "work_y": mi.rcWork.top,
        "work_width": mi.rcWork.right - mi.rcWork.left,
        "work_height": mi.rcWork.bottom - mi.rcWork.top,
    }
    _monitors.append(monitor)
    return True


def detect_monitors():
    """Detect monitors using Windows API directly."""
    global _monitors
    _monitors = []

    callback = MONITORENUMPROC(_enum_callback)
    result = EnumDisplayMonitors(None, None, callback, 0)

    if not result:
        return {"count": 0, "monitors": [], "error": "EnumDisplayMonitors failed"}

    # Remove handle from JSON output
    output = []
    for m in _monitors:
        output.append({k: v for k, v in m.items() if k != "handle"})

    return {
        "count": len(output),
        "monitors": output,
        "source": "Windows EnumDisplayMonitors (native ctypes)"
    }


def get_monitor(monitor_id=1):
    """Get specific monitor by ID."""
    info = detect_monitors()
    monitors = info.get("monitors", [])
    if monitor_id - 1 < len(monitors):
        return monitors[monitor_id - 1]
    return monitors[0] if monitors else None


if __name__ == "__main__":
    info = detect_monitors()
    print(json.dumps(info, indent=2))
