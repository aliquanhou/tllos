#!/usr/bin/env python3
"""
TLL OS Native Screenshot

Uses ctypes to call Windows GDI APIs.
No PySide6 dependency.
"""

import ctypes
import hashlib
from ctypes import wintypes
from pathlib import Path
from datetime import datetime

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# Constants
SRCCOPY = 0x00CC0020
BI_RGB = 0
DIB_RGB_COLORS = 0


def get_screen_size():
    """Get screen size using Windows API."""
    width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
    height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
    return width, height


def capture_screen_to_file(output_path, monitor_x=0, monitor_y=0):
    """Capture screen using Windows GDI APIs."""
    width, height = get_screen_size()

    # Get DC
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)

    # Create bitmap
    hbm = gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
    gdi32.SelectObject(hdc_mem, hbm)

    # BitBlt
    gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, monitor_x, monitor_y, SRCCOPY)

    # Save as BMP
    # Use simpler approach: get bitmap bits and save
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

    class BITMAPFILEHEADER(ctypes.Structure):
        _fields_ = [
            ("bfType", wintypes.WORD),
            ("bfSize", wintypes.DWORD),
            ("bfReserved1", wintypes.WORD),
            ("bfReserved2", wintypes.WORD),
            ("bfOffBits", wintypes.DWORD),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = height
    bmi.biPlanes = 1
    bmi.biBitCount = 24
    bmi.biCompression = BI_RGB

    row_size = ((width * 24 + 31) // 32) * 4
    image_size = row_size * height

    buffer = ctypes.create_string_buffer(image_size)
    gdi32.GetDIBits(hdc_mem, hbm, 0, height, buffer, ctypes.byref(bmi), DIB_RGB_COLORS)

    # Write BMP file
    bfh = BITMAPFILEHEADER()
    bfh.bfType = 0x4D42  # "BM"
    bfh.bfSize = ctypes.sizeof(BITMAPFILEHEADER) + ctypes.sizeof(BITMAPINFOHEADER) + image_size
    bfh.bfOffBits = ctypes.sizeof(BITMAPFILEHEADER) + ctypes.sizeof(BITMAPINFOHEADER)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, 'wb') as f:
        f.write(bfh)
        f.write(bmi)
        f.write(buffer)

    # Cleanup
    gdi32.DeleteObject(hbm)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)

    # Compute hash
    with open(output, 'rb') as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    return {
        "path": str(output),
        "width": width,
        "height": height,
        "hash": sha,
        "timestamp": datetime.now().isoformat(),
        "source": "Windows GDI (native ctypes)"
    }


if __name__ == "__main__":
    result = capture_screen_to_file("screenshots/native_test.bmp")
    print(f"Screenshot: {result['path']}")
    print(f"Size: {result['width']}x{result['height']}")
    print(f"Hash: {result['hash'][:16]}...")
