#!/usr/bin/env python3
"""
TLL OS Native Window Host

Shows TLL Framebuffer in a real Windows window.
Pure ctypes + Win32 API. No Qt/No PySide6.
"""

import ctypes
import ctypes.wintypes as wintypes
import time
from typing import Optional, Callable

from ..framebuffer import TLLFramebuffer

# Win32 constants
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
WM_DESTROY = 0x0002
WM_PAINT = 0x000F
WM_KEYDOWN = 0x0100
WM_CHAR = 0x0102
WM_CLOSE = 0x0010
WM_TIMER = 0x0113
VK_RETURN = 0x0D
VK_BACK = 0x08
VK_ESCAPE = 0x1B

CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001

SW_SHOW = 5

GWL_WNDPROC = -4

# gdi32
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0


# Custom structs
class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", wintypes.HDC),
        ("fErase", wintypes.BOOL),
        ("rcPaint", wintypes.RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", ctypes.c_byte * 32),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class TLLENativeWindowHost:
    """Native Windows window that displays TLL Framebuffer."""

    def __init__(self, framebuffer: TLLFramebuffer,
                 title: str = "TLL OS",
                 on_key_callback: Optional[Callable[[str], None]] = None,
                 on_command_callback: Optional[Callable[[str], None]] = None):
        self.fb = framebuffer
        self.title = title
        self.on_key = on_key_callback
        self.on_command = on_command_callback

        self.hwnd = None
        self.running = False
        self.input_buffer = ""
        self.input_callback = on_command_callback

        # Win32
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32

        # Set up function signatures
        self._setup_win32_signatures()

    def _setup_win32_signatures(self):
        """Set up Win32 function signatures to avoid overflow."""
        self.user32.CreateWindowExW.restype = wintypes.HWND
        self.user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
            wintypes.DWORD, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, wintypes.HWND,
            wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
        ]

        self.user32.DefWindowProcW.restype = ctypes.c_long
        self.user32.DefWindowProcW.argtypes = [
            wintypes.HWND, wintypes.UINT,
            wintypes.WPARAM, wintypes.LPARAM
        ]

        self.user32.BeginPaint.restype = wintypes.HDC
        self.user32.BeginPaint.argtypes = [wintypes.HWND, ctypes.c_void_p]

        self.user32.EndPaint.argtypes = [wintypes.HWND, ctypes.c_void_p]

        self.user32.GetMessageW.restype = wintypes.BOOL
        self.user32.GetMessageW.argtypes = [
            ctypes.POINTER(wintypes.MSG), wintypes.HWND,
            wintypes.UINT, wintypes.UINT
        ]

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure."""
        if msg == WM_PAINT:
            self._on_paint(hwnd)
            return 0
        elif msg == WM_KEYDOWN:
            self._on_keydown(wparam)
            return 0
        elif msg == WM_CHAR:
            self._on_char(wparam)
            return 0
        elif msg == WM_DESTROY:
            self.running = False
            self.user32.PostQuitMessage(0)
            return 0
        elif msg == WM_CLOSE:
            self.user32.DestroyWindow(hwnd)
            return 0

        return self.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _on_paint(self, hwnd):
        """Paint framebuffer to window."""
        ps = PAINTSTRUCT()
        hdc = self.user32.BeginPaint(hwnd, ctypes.byref(ps))

        # Get pixel data from framebuffer
        pixels = self.fb.get_pixel_data()
        h, w = pixels.shape[:2]

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = w
        bmi.biHeight = -h  # Top-down
        bmi.biPlanes = 1
        bmi.biBitCount = 24
        bmi.biCompression = BI_RGB
        bmi.biSizeImage = 0

        # Use SetDIBitsToDevice
        pixel_bytes = pixels.tobytes()
        self.gdi32.SetDIBitsToDevice(
            hdc, 0, 0, w, h, 0, 0, 0, h,
            pixel_bytes, ctypes.byref(bmi), DIB_RGB_COLORS
        )

        self.user32.EndPaint(hwnd, ctypes.byref(ps))

    def _on_keydown(self, vkey):
        """Handle key down."""
        if vkey == VK_RETURN:
            if self.input_callback and self.input_buffer:
                self.input_callback(self.input_buffer)
                self.input_buffer = ""
        elif vkey == VK_BACK:
            self.input_buffer = self.input_buffer[:-1]
        elif vkey == VK_ESCAPE:
            self.running = False

        # Trigger repaint
        self.user32.InvalidateRect(self.hwnd, None, True)

    def _on_char(self, char_code):
        """Handle char input."""
        if 32 <= char_code <= 126:  # Printable ASCII
            self.input_buffer += chr(char_code)
            self.user32.InvalidateRect(self.hwnd, None, True)

    def create_window(self):
        """Create the native window."""
        # Register window class
        wc = wintypes.WNDCLASSW()
        wc.lpfnWndProc = ctypes.WINFUNCTYPE(
            ctypes.c_long, wintypes.HWND, wintypes.UINT,
            wintypes.WPARAM, wintypes.LPARAM
        )(self._wnd_proc)
        wc.hInstance = self.user32.GetModuleHandleW(None)
        wc.lpszClassName = "TLLOSWindow"

        self.user32.RegisterClassW(ctypes.byref(wc))

        # Create window
        self.hwnd = self.user32.CreateWindowExW(
            0,
            "TLLOSWindow",
            self.title,
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            100, 100,
            self.fb.width + 16, self.fb.height + 39,
            None, None, wc.hInstance, None
        )

        if not self.hwnd:
            raise Exception("Failed to create window")

        self.user32.ShowWindow(self.hwnd, SW_SHOW)
        self.user32.UpdateWindow(self.hwnd)

    def run(self):
        """Run the message loop."""
        self.running = True
        msg = wintypes.MSG()

        while self.running:
            # Render frame
            self.user32.InvalidateRect(self.hwnd, None, True)
            self.user32.UpdateWindow(self.hwnd)

            # Process messages (non-blocking for one frame)
            while self.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                if msg.message == 0x0012:  # WM_QUIT
                    self.running = False
                    break
                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageW(ctypes.byref(msg))

            time.sleep(0.1)  # 10 FPS

    def close(self):
        """Close the window."""
        self.running = False
        if self.hwnd:
            self.user32.DestroyWindow(self.hwnd)
