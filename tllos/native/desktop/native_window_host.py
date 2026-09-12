#!/usr/bin/env python3
"""
TLL OS Native Window Host

Pure Win32 API window via ctypes.
NO PySide6, NO Qt, NO Electron, NO WebView.
"""

import ctypes
import sys
from ctypes import wintypes

# Windows API
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# Set proper function signatures to avoid overflow
user32.DefWindowProcW.restype = ctypes.c_long
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.BeginPaint.restype = wintypes.HDC
user32.EndPaint.argtypes = [wintypes.HWND, ctypes.c_void_p]
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.c_void_p]
user32.FillRect.restype = ctypes.c_int
user32.FillRect.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.HBRUSH]
gdi32.SetTextColor.restype = wintypes.COLORREF
gdi32.SetBkMode.restype = ctypes.c_int
gdi32.CreateSolidBrush.restype = wintypes.HBRUSH
gdi32.Ellipse.restype = wintypes.BOOL
gdi32.TextOutW.restype = wintypes.BOOL
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]

# Constants
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
CW_USEDEFAULT = 0x80000000
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000

WM_DESTROY = 0x0002
WM_PAINT = 0x000F
WM_CLOSE = 0x0010

SW_SHOW = 5

COLOR_WINDOW = 5
DT_CENTER = 0x00000001
DT_VCENTER = 0x00000004
DT_SINGLELINE = 0x00000020

# Colors (BGR)
CLR_BG = 0x202020       # Dark gray
CLR_GREEN = 0x00FF00    # Green
CLR_WHITE = 0xFFFFFF    # White
CLR_BLUE = 0xFF0000     # Blue
CLR_PANEL = 0x303030    # Panel gray


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", wintypes.HDC),
        ("fErase", wintypes.BOOL),
        ("rcPaint", RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", wintypes.BYTE * 32),
    ]


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]


# WindowProc callback type
WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,  # LRESULT
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
)


def draw_text(hdc, x, y, w, h, text, color=CLR_WHITE):
    """Draw text centered in rect."""
    old_color = gdi32.SetTextColor(hdc, color)
    old_bk = gdi32.SetBkMode(hdc, 1)  # TRANSPARENT
    rect = RECT(x, y, x + w, y + h)
    user32.DrawTextW(hdc, text, -1, ctypes.byref(rect), DT_CENTER | DT_VCENTER | DT_SINGLELINE)
    gdi32.SetTextColor(hdc, old_color)


def fill_rect(hdc, x, y, w, h, color):
    """Fill rect with color."""
    brush = gdi32.CreateSolidBrush(color)
    rect = RECT(x, y, x + w, y + h)
    user32.FillRect(hdc, ctypes.byref(rect), brush)
    gdi32.DeleteObject(brush)


def window_proc(hwnd, msg, wparam, lparam):
    """Window procedure."""
    if msg == WM_PAINT:
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))

        # Get client rect
        rect = RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        cw = rect.right - rect.left
        ch = rect.bottom - rect.top

        # Background
        fill_rect(hdc, 0, 0, cw, ch, CLR_BG)

        # Title bar
        fill_rect(hdc, 0, 0, cw, 50, 0x101010)
        draw_text(hdc, 0, 0, cw, 50, "TLL DESKTOP AGENT", CLR_WHITE)

        # Status light (green circle)
        gdi32.Ellipse(hdc, 20, 15, 40, 35)
        old_brush = gdi32.SelectObject(hdc, gdi32.GetStockObject(0))  # BLACK_BRUSH
        brush = gdi32.CreateSolidBrush(CLR_GREEN)
        gdi32.SelectObject(hdc, brush)
        gdi32.Ellipse(hdc, 20, 15, 40, 35)
        gdi32.DeleteObject(brush)
        draw_text(hdc, 50, 10, 200, 30, "SYSTEM ONLINE", CLR_GREEN)

        # VISION panel
        py = 70
        fill_rect(hdc, 10, py, cw - 20, 120, CLR_PANEL)
        draw_text(hdc, 10, py + 5, cw - 20, 25, "VISION", CLR_BLUE)
        draw_text(hdc, 10, py + 35, cw - 20, 80, "[ Live Screenshot Area ]", 0x808080)

        # BRAIN panel
        py = 200
        fill_rect(hdc, 10, py, cw - 20, 80, CLR_PANEL)
        draw_text(hdc, 10, py + 5, cw - 20, 25, "BRAIN", CLR_BLUE)
        draw_text(hdc, 10, py + 35, cw - 20, 40, "Goal: Open Notepad  |  State: THINKING", CLR_WHITE)

        # PLAN panel
        py = 290
        fill_rect(hdc, 10, py, cw - 20, 80, CLR_PANEL)
        draw_text(hdc, 10, py + 5, cw - 20, 25, "PLAN", CLR_BLUE)
        draw_text(hdc, 10, py + 35, cw - 20, 40, "1. OBSERVE  2. SELECT  3. EXECUTE  4. VERIFY", CLR_WHITE)

        # ACTION panel
        py = 380
        fill_rect(hdc, 10, py, cw - 20, 60, CLR_PANEL)
        draw_text(hdc, 10, py + 5, cw - 20, 25, "ACTION", CLR_BLUE)
        draw_text(hdc, 10, py + 30, cw - 20, 25, "Permission: WAIT_APPROVAL", CLR_GREEN)

        user32.EndPaint(hwnd, ctypes.byref(ps))
        return 0

    elif msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0

    elif msg == WM_CLOSE:
        user32.DestroyWindow(hwnd)
        return 0

    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


# Keep reference to prevent GC
_wndproc_ref = WNDPROC(window_proc)


def create_native_window(title="TLL OS Desktop Agent", width=800, height=600):
    """Create native Win32 window."""
    hInstance = kernel32.GetModuleHandleW(None)

    # Register window class
    wc = WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
    wc.style = CS_HREDRAW | CS_VREDRAW
    wc.lpfnWndProc = ctypes.cast(_wndproc_ref, ctypes.c_void_p)
    wc.hInstance = hInstance
    wc.hCursor = user32.LoadCursorW(None, 32512)  # IDC_ARROW
    wc.hbrBackground = gdi32.CreateSolidBrush(CLR_BG)
    wc.lpszClassName = "TLLAgentWindow"

    atom = user32.RegisterClassExW(ctypes.byref(wc))
    if not atom:
        print(f"RegisterClassEx failed: {kernel32.GetLastError()}")
        return None

    # Create window
    hwnd = user32.CreateWindowExW(
        0,
        "TLLAgentWindow",
        title,
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT,
        width, height,
        None, None, hInstance, None
    )

    if not hwnd:
        print(f"CreateWindowEx failed: {kernel32.GetLastError()}")
        return None

    user32.ShowWindow(hwnd, SW_SHOW)
    user32.UpdateWindow(hwnd)

    return hwnd


def run_message_loop():
    """Run Win32 message loop."""
    msg = MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


if __name__ == "__main__":
    print("TLL OS Native Window")
    print("Creating window...")
    hwnd = create_native_window()
    if hwnd:
        print(f"Window created: hwnd={hwnd}")
        print("Running message loop...")
        run_message_loop()
    else:
        print("Failed to create window")
        sys.exit(1)
