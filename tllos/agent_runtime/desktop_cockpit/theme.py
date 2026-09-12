#!/usr/bin/env python3
"""
TLL OS Desktop Cockpit - Theme

Dark theme for the cockpit.
"""

DARK_THEME = """
    QMainWindow {
        background-color: #1a1a2e;
        color: #e0e0e0;
    }
    QWidget {
        background-color: #1a1a2e;
        color: #e0e0e0;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QGroupBox {
        border: 1px solid #16213e;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: bold;
        color: #0f3460;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
    QPushButton {
        background-color: #0f3460;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        color: white;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #16213e;
    }
    QPushButton:pressed {
        background-color: #e94560;
    }
    QLabel {
        color: #e0e0e0;
    }
"""
