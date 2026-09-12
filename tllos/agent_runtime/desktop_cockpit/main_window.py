#!/usr/bin/env python3
"""
TLL OS Desktop Agent Cockpit - Main Window

PySide6 GUI Cockpit.
"""

import sys
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent

sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "controllers"))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QPushButton, QGridLayout, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPixmap

from theme import DARK_THEME
from state_controller import StateController


class StatusWidget(QGroupBox):
    def __init__(self):
        super().__init__("STATUS")
        layout = QVBoxLayout()
        self.status_label = QLabel("🟢 RUNNING")
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ff88;")
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def update_status(self, state):
        pass


class VisionWidget(QGroupBox):
    def __init__(self):
        super().__init__("👁 VISION")
        layout = QVBoxLayout()
        # Screenshot preview
        self.screenshot_label = QLabel("No screenshot")
        self.screenshot_label.setAlignment(Qt.AlignCenter)
        self.screenshot_label.setMinimumSize(320, 180)
        self.screenshot_label.setStyleSheet("border: 1px solid #333; background: #000;")
        layout.addWidget(self.screenshot_label)
        # Info labels
        self.frame_label = QLabel("Frame: --")
        self.objects_label = QLabel("Objects: 0")
        self.hash_label = QLabel("Hash: --")
        layout.addWidget(self.frame_label)
        layout.addWidget(self.objects_label)
        layout.addWidget(self.hash_label)
        self.setLayout(layout)

    def update_data(self, vision, screenshot_path=None):
        self.frame_label.setText(f"Frame: {vision.get('frame', '--')}")
        self.objects_label.setText(f"Objects: {vision.get('objects', 0)}")
        self.hash_label.setText(f"Hash: {vision.get('hash', '--')}")
        # Load screenshot if available
        if screenshot_path and Path(screenshot_path).exists():
            pixmap = QPixmap(str(screenshot_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(320, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.screenshot_label.setPixmap(scaled)
                self.screenshot_label.setText("")
            else:
                self.screenshot_label.setText("Failed to load image")
        else:
            self.screenshot_label.setText("No screenshot")


class ReasoningWidget(QGroupBox):
    def __init__(self):
        super().__init__("🧠 REASONING")
        layout = QGridLayout()
        self.goal_label = QLabel("Goal: --")
        self.decision_label = QLabel("Decision: --")
        self.confidence_label = QLabel("Confidence: 0.0")
        layout.addWidget(self.goal_label, 0, 0)
        layout.addWidget(self.decision_label, 1, 0)
        layout.addWidget(self.confidence_label, 2, 0)
        self.setLayout(layout)

    def update_data(self, reasoning):
        self.goal_label.setText(f"Goal: {reasoning.get('goal', '--')}")
        self.decision_label.setText(f"Decision: {reasoning.get('decision', '--')}")
        conf = reasoning.get('confidence', 0.0)
        self.confidence_label.setText(f"Confidence: {conf:.2f}")


class PlanWidget(QGroupBox):
    def __init__(self):
        super().__init__("📋 PLAN")
        layout = QVBoxLayout()
        self.steps_label = QLabel("No plan")
        layout.addWidget(self.steps_label)
        self.setLayout(layout)

    def update_data(self, plan):
        steps = plan.get('steps', [])
        current = plan.get('current_step', 0)
        if not steps:
            self.steps_label.setText("No plan")
            return
        lines = []
        for i, step in enumerate(steps):
            marker = "→" if i == current else " "
            lines.append(f"{marker} {i+1}. {step}")
        self.steps_label.setText("\n".join(lines))


class ActionWidget(QGroupBox):
    def __init__(self):
        super().__init__("🖱 ACTION")
        layout = QGridLayout()
        self.current_label = QLabel("Last: --")
        self.result_label = QLabel("Result: --")
        self.hash_label = QLabel("Hash: --")
        layout.addWidget(self.current_label, 0, 0)
        layout.addWidget(self.result_label, 1, 0)
        layout.addWidget(self.hash_label, 2, 0)
        self.setLayout(layout)

    def update_data(self, action):
        self.current_label.setText(f"Last: {action.get('current', '--')}")
        self.result_label.setText(f"Result: {action.get('result', '--')}")
        self.hash_label.setText(f"Hash: {action.get('before_hash', '--')[:16]}")


class EvidenceWidget(QGroupBox):
    def __init__(self):
        super().__init__("🔐 EVIDENCE")
        layout = QGridLayout()
        self.sha_label = QLabel("SHA256: --")
        self.time_label = QLabel("Time: --")
        layout.addWidget(self.sha_label, 0, 0)
        layout.addWidget(self.time_label, 1, 0)
        self.setLayout(layout)

    def update_data(self, timestamp):
        self.time_label.setText(f"Time: {timestamp[:19] if timestamp else '--'}")


class TimelineWidget(QGroupBox):
    def __init__(self):
        super().__init__("📜 AGENT TIMELINE")
        layout = QVBoxLayout()
        self.timeline = QTextEdit()
        self.timeline.setReadOnly(True)
        self.timeline.setMaximumHeight(120)
        layout.addWidget(self.timeline)
        self.setLayout(layout)

    def add_event(self, event):
        current = self.timeline.toPlainText()
        lines = current.split("\n")[-9:]  # Keep last 10
        lines.append(event)
        self.timeline.setPlainText("\n".join(lines))


class ReplayWidget(QGroupBox):
    def __init__(self):
        super().__init__("⏮ REPLAY")
        layout = QHBoxLayout()
        self.prev_btn = QPushButton("⏮ Prev")
        self.play_btn = QPushButton("▶ Replay")
        self.next_btn = QPushButton("Next ⏭")
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.play_btn)
        layout.addWidget(self.next_btn)
        self.setLayout(layout)


class ControlPanel(QGroupBox):
    def __init__(self):
        super().__init__("CONTROLS")
        layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ START")
        self.pause_btn = QPushButton("Ⅱ PAUSE")
        self.stop_btn = QPushButton("■ STOP")
        self.approve_btn = QPushButton("✓ APPROVE")
        self.deny_btn = QPushButton("✕ DENY")
        layout.addWidget(self.start_btn)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.approve_btn)
        layout.addWidget(self.deny_btn)
        self.setLayout(layout)


class CockpitWindow(QMainWindow):
    def __init__(self, monitor=2):
        super().__init__()
        self.setWindowTitle("TLL DESKTOP AGENT COCKPIT")
        self.resize(500, 700)

        self.controller = StateController(PROJECT_ROOT)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Title
        title = QLabel("TLL DESKTOP AGENT COCKPIT")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e94560; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Widgets
        self.status_widget = StatusWidget()
        self.vision_widget = VisionWidget()
        self.reasoning_widget = ReasoningWidget()
        self.plan_widget = PlanWidget()
        self.action_widget = ActionWidget()
        self.evidence_widget = EvidenceWidget()
        self.timeline_widget = TimelineWidget()
        self.replay_widget = ReplayWidget()
        self.control_panel = ControlPanel()

        main_layout.addWidget(self.status_widget)
        main_layout.addWidget(self.vision_widget)
        main_layout.addWidget(self.reasoning_widget)
        main_layout.addWidget(self.plan_widget)
        main_layout.addWidget(self.action_widget)
        main_layout.addWidget(self.evidence_widget)
        main_layout.addWidget(self.timeline_widget)
        main_layout.addWidget(self.replay_widget)
        main_layout.addWidget(self.control_panel)

        # Timer for refresh
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)  # Refresh every 2 seconds

        # Move to specified monitor
        self.move_to_monitor(monitor)

        self.timeline_widget.add_event("Cockpit started")

    def move_to_monitor(self, monitor_num):
        screens = self.screen().virtualSiblings() if hasattr(self.screen(), 'virtualSiblings') else []
        try:
            from PySide6.QtWidgets import QApplication
            screens = QApplication.screens()
            if monitor_num < len(screens):
                screen = screens[monitor_num - 1]
                geo = screen.geometry()
                self.move(geo.x() + 50, geo.y() + 50)
        except Exception as e:
            print(f"Monitor positioning error: {e}")

    def refresh(self):
        state = self.controller.get_full_state()
        # Find latest screenshot PNG
        frames_dir = PROJECT_ROOT / "tllos" / "agent_runtime" / "desktop_vision_runtime" / "frames"
        screenshot_path = None
        if frames_dir.exists():
            png_files = sorted(frames_dir.glob("*.png"), key=lambda f: f.stat().st_mtime, reverse=True)
            if png_files:
                screenshot_path = png_files[0]
        self.vision_widget.update_data(state['vision'], screenshot_path)
        self.reasoning_widget.update_data(state['reasoning'])
        self.plan_widget.update_data(state['plan'])
        self.action_widget.update_data(state['action'])
        self.evidence_widget.update_data(state['timestamp'])


def main():
    parser = argparse.ArgumentParser(description="TLL Desktop Agent Cockpit")
    parser.add_argument("--monitor", type=int, default=2, help="Monitor number (1 or 2)")
    args = parser.parse_args()

    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    window = CockpitWindow(monitor=args.monitor)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
