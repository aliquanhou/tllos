#!/usr/bin/env python3
"""
TLL OS Native Font Runtime

Built-in bitmap fonts, no external font files.
Pure Python, no PIL font dependency.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np


class TLLFont:
    """TLL Native Font - built-in bitmap glyphs."""

    def __init__(self):
        self.ascii_font = self._load_ascii_font()
        self.chinese_font = self._load_chinese_font()
        self.font_name = "TLL-Builtin-1.0"

    def _load_ascii_font(self) -> Dict[str, np.ndarray]:
        """Load built-in 8x16 ASCII font."""
        # Classic 8x16 bitmap font (simplified)
        font = {}

        # Space
        font[' '] = np.zeros((16, 8), dtype=np.uint8)

        # A-Z (simplified 8x16)
        for i in range(26):
            char = chr(ord('A') + i)
            font[char] = self._make_ascii_glyph(char)

        # a-z
        for i in range(26):
            char = chr(ord('a') + i)
            font[char] = self._make_ascii_glyph(char.upper())  # Simplified: use upper shape

        # 0-9
        for i in range(10):
            char = str(i)
            font[char] = self._make_ascii_glyph(char)

        # Punctuation
        for char in '.:,;-_()[]{}!?@#$%^&*+=<>/\\|':
            font[char] = self._make_ascii_glyph(char)

        return font

    def _make_ascii_glyph(self, char: str) -> np.ndarray:
        """Generate a real 8x16 ASCII glyph using 5x7 font."""
        # Classic 5x7 font table
        font5x7 = {
            'A': [0x7E,0x11,0x11,0x11,0x7E],
            'B': [0x7F,0x49,0x49,0x49,0x36],
            'C': [0x3E,0x41,0x41,0x41,0x22],
            'D': [0x7F,0x41,0x41,0x22,0x1C],
            'E': [0x7F,0x49,0x49,0x49,0x41],
            'F': [0x7F,0x09,0x09,0x09,0x01],
            'G': [0x3E,0x41,0x49,0x49,0x7A],
            'H': [0x7F,0x08,0x08,0x08,0x7F],
            'I': [0x00,0x41,0x7F,0x41,0x00],
            'J': [0x20,0x40,0x41,0x3F,0x01],
            'K': [0x7F,0x08,0x14,0x22,0x41],
            'L': [0x7F,0x40,0x40,0x40,0x40],
            'M': [0x7F,0x02,0x0C,0x02,0x7F],
            'N': [0x7F,0x04,0x08,0x10,0x7F],
            'O': [0x3E,0x41,0x41,0x41,0x3E],
            'P': [0x7F,0x09,0x09,0x09,0x06],
            'Q': [0x3E,0x41,0x51,0x21,0x5E],
            'R': [0x7F,0x09,0x19,0x29,0x46],
            'S': [0x46,0x49,0x49,0x49,0x31],
            'T': [0x01,0x01,0x7F,0x01,0x01],
            'U': [0x3F,0x40,0x40,0x40,0x3F],
            'V': [0x1F,0x20,0x40,0x20,0x1F],
            'W': [0x3F,0x40,0x38,0x40,0x3F],
            'X': [0x63,0x14,0x08,0x14,0x63],
            'Y': [0x07,0x08,0x70,0x08,0x07],
            'Z': [0x61,0x51,0x49,0x45,0x43],
            '0': [0x3E,0x51,0x49,0x45,0x3E],
            '1': [0x00,0x42,0x7F,0x40,0x00],
            '2': [0x42,0x61,0x51,0x49,0x46],
            '3': [0x21,0x41,0x45,0x4B,0x31],
            '4': [0x18,0x14,0x12,0x7F,0x10],
            '5': [0x27,0x45,0x45,0x45,0x39],
            '6': [0x3C,0x4A,0x49,0x49,0x30],
            '7': [0x01,0x71,0x09,0x05,0x03],
            '8': [0x36,0x49,0x49,0x49,0x36],
            '9': [0x06,0x49,0x49,0x29,0x1E],
            ' ': [0x00,0x00,0x00,0x00,0x00],
            '.': [0x00,0x60,0x60,0x00,0x00],
            ',': [0x00,0x80,0x60,0x00,0x00],
            ':': [0x00,0x36,0x36,0x00,0x00],
            ';': [0x00,0x80,0x76,0x00,0x00],
            '!': [0x00,0x7F,0x40,0x00,0x00],
            '?': [0x02,0x01,0x51,0x09,0x06],
            '-': [0x08,0x08,0x08,0x08,0x08],
            '_': [0x40,0x40,0x40,0x40,0x40],
            '/': [0x20,0x10,0x08,0x04,0x02],
            '\\': [0x02,0x04,0x08,0x10,0x20],
            '(': [0x00,0x1C,0x22,0x41,0x00],
            ')': [0x00,0x41,0x22,0x1C,0x00],
            '[': [0x00,0x7F,0x41,0x41,0x00],
            ']': [0x00,0x41,0x41,0x7F,0x00],
            '<': [0x08,0x14,0x22,0x41,0x00],
            '>': [0x00,0x41,0x22,0x14,0x08],
            '=': [0x14,0x14,0x14,0x14,0x14],
            '+': [0x08,0x08,0x7F,0x08,0x08],
            '*': [0x14,0x08,0x7F,0x08,0x14],
            '&': [0x32,0x49,0x49,0x3E,0x40],
            '@': [0x3E,0x41,0x5D,0x55,0x4E],
            '#': [0x14,0x7F,0x14,0x7F,0x14],
            '%': [0x23,0x13,0x08,0x64,0x62],
            '^': [0x08,0x04,0x02,0x04,0x08],
            '~': [0x08,0x14,0x08,0x14,0x08],
            '|': [0x00,0x7F,0x00,0x7F,0x00],
            "'": [0x00,0x03,0x04,0x00,0x00],
            '"': [0x00,0x03,0x00,0x03,0x00],
            '`': [0x00,0x01,0x02,0x00,0x00],
            '{': [0x00,0x1F,0x21,0x21,0x00],
            '}': [0x00,0x21,0x21,0x1F,0x00],
        }

        glyph = np.zeros((16, 8), dtype=np.uint8)
        char_upper = char.upper()

        if char_upper in font5x7:
            pattern = font5x7[char_upper]
            # 5x7 font: pattern has 5 bytes (columns), each byte has 7 bits (rows)
            # Center 5x7 in 8x16
            for col in range(5):
                bits = pattern[col]
                for row in range(7):
                    if bits & (1 << row):
                        glyph[row + 4, col + 1] = 1
        else:
            # Unknown char - draw a question mark
            pattern = font5x7['?']
            for col in range(5):
                bits = pattern[col]
                for row in range(7):
                    if bits & (1 << row):
                        glyph[row + 4, col + 1] = 1

        return glyph

    def _load_chinese_font(self) -> Dict[str, np.ndarray]:
        """Load built-in common Chinese glyphs (16x16)."""
        font = {}

        # Common characters needed for TLL OS
        chars = [
            '智', '能', '代', '理', '系', '统', '状', '态',
            '任', '务', '执', '行', '等', '待', '完', '成',
            '错', '误', '开', '始', '停', '止', '在', '线',
            '窗', '口', '面', '板', '背', '景', '前', '景',
            '文', '字', '显', '示', '控', '制', '批', '准',
            '拒', '绝', '新', '建', '打', '开', '关', '闭',
            '文', '件', '目', '录', '编', '辑', '保', '存',
        ]

        for char in chars:
            font[char] = self._make_chinese_glyph(char)

        return font

    def _make_chinese_glyph(self, char: str) -> np.ndarray:
        """Generate a simple 16x16 Chinese glyph."""
        glyph = np.zeros((16, 16), dtype=np.uint8)

        # Simple pattern based on char code
        code = ord(char)
        for y in range(16):
            for x in range(16):
                if (code * (y + 7) * (x + 11)) % 5 == 0:
                    glyph[y, x] = 1

        # Add some structure (top/bottom bars)
        glyph[2, 2:14] = 1
        glyph[13, 2:14] = 1

        return glyph

    def get_glyph(self, char: str) -> Optional[np.ndarray]:
        """Get glyph bitmap for character."""
        # Try Chinese first (larger)
        if char in self.chinese_font:
            return self.chinese_font[char]
        # Then ASCII
        if char in self.ascii_font:
            return self.ascii_font[char]
        # Fallback: space
        return self.ascii_font.get(' ')

    def get_text_dimensions(self, text: str) -> Tuple[int, int]:
        """Calculate text dimensions."""
        width = 0
        height = 0
        for char in text:
            glyph = self.get_glyph(char)
            if glyph is not None:
                h, w = glyph.shape
                width += w + 1  # 1px spacing
                height = max(height, h)
        return width, height
