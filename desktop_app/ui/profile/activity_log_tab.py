# desktop_app/ui/profile/activity_log_tab.py

from __future__ import annotations

import csv
from typing import Any, Dict, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView

from desktop_app.utils.api_wrapper import get_api


class ActivityLogTab(QWidget):
    """
    Reusable Activity Log UI.

    Used in:
    - ProfilePage (Activity tab)
    - ActivityPage (full page wrapper)

    Behavior:
    - Tries to load real logs via API.
    - Falls back to sample data if not available.
    """

    HEADERS = ["Date", "User", "Action", "Details"]

    def __init__(self, user_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.api = get_api()

        self.table: Optional[QTableWidget] = None
        self.export_btn: Optional[QPushButton] = None
        self.refresh_btn: Optional[QPushButton] = None

        self._init_ui()
        self.refresh()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        title = QLabel("Activity Log")
        title.setObjectName("title")
        root.addWidget(title)

        # Action row
        actions = QHBoxLayout()
        actions.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("secondaryBtn")
        self.refresh_btn.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_btn)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setObjectName("ghost")
        self.export_btn.clicked.connect(self.export_csv)
        actions.addWidget(self.export_btn)

        root.addLayout(actions)

        # Table
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.table.horizontalHeader().setStretchLastSection(True)
        try:
            self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        except Exception:
            pass

        # ✅ cleaner vertical behavior
        try:
            vh = self.table.verticalHeader()
            vh.setVisible(False)
            vh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        except Exception:
            pass

        root.addWidget(self.table, 1)

    # ---------------------------------------------------------
    # Data
    # ---------------------------------------------------------
    def refresh(self):
        if not self.table:
            return

        rows = self._fetch_logs_safely(limit=50)

        if not rows:
            rows = self._sample_rows()

        self._render_rows(rows)

    def _fetch_logs_safely(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            user_id = self.user.get("id", 0) or 0
            data = self.api.get_user_logs(user_id, limit=limit) or {}
            logs = data.get("logs", []) or []

            normalized: List[Dict[str, Any]] = []
            for log in logs:
                normalized.append({
                    "timestamp": log.get("timestamp") or log.get("date") or "",
                    "username": log.get("username") or log.get("user") or self.user.get("username", ""),
                    "action": log.get("action") or log.get("event") or "",
                    "details": log.get("message") or log.get("details") or ""
                })

            return normalized
        except Exception:
            return []

    def _sample_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": "2025-12-01 09:12",
                "username": "admin",
                "action": "create_user",
                "details": "Created user: john"
            },
            {
                "timestamp": "2025-12-01 10:00",
                "username": "manager",
                "action": "update_product",
                "details": "Updated: Soda 300ml"
            },
            {
                "timestamp": "2025-12-02 11:30",
                "username": "retailer1",
                "action": "sale",
                "details": "Sale ID: 124"
            },
        ]

    def _render_rows(self, rows: List[Dict[str, Any]]):
        if not self.table:
            return

        self.table.setRowCount(0)

        for r, row in enumerate(rows):
            self.table.insertRow(r)

            values = [
                row.get("timestamp", ""),
                row.get("username", ""),
                row.get("action", ""),
                row.get("details", ""),
            ]

            for c, v in enumerate(values):
                item = QTableWidgetItem(str(v))
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(r, c, item)

        try:
            self.table.resizeColumnsToContents()
        except Exception:
            pass

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------
    def export_csv(self):
        if not self.table:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Activity Log",
            "activity_log.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.HEADERS)

                for r in range(self.table.rowCount()):
                    row_vals = []
                    for c in range(self.table.columnCount()):
                        item = self.table.item(r, c)
                        row_vals.append(item.text() if item else "")
                    writer.writerow(row_vals)

            QMessageBox.information(self, "Export Complete", f"CSV saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
