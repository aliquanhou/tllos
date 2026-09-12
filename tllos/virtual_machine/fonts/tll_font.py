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
        """Generate a simple 8x16 ASCII glyph."""
        glyph = np.zeros((16, 8), dtype=np.uint8)

        # Simple pattern based on char code
        code = ord(char)
        for y in range(16):
            for x in range(8):
                # Pseudo-random but deterministic pattern
                if (code * (y + 3) * (x + 5)) % 7 == 0:
                    glyph[y, x] = 1

        # Make it look like a letter (top and bottom bars)
        glyph[2, :] = 1
        glyph[14, :] = 1

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
