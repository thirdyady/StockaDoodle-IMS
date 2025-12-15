# desktop_app/ui/pages/activity.py

from __future__ import annotations

import csv
import traceback
from typing import Any, Dict, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView

from desktop_app.utils.api_wrapper import get_api


class ActivityPage(QWidget):
    """
    Admin-only Activity Page (Full Logs).

    Goals:
    - When Dashboard "View More" is clicked, user sees FULL and POPULATED logs page.
    - Robust against API shape differences.
    - Method filters + search + export.
    - Table should visually fill space cleanly every page.
    """

    PAGE_SIZE = 10

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.role = (self.user.get("role") or "").lower()
        self.api = get_api()

        self._all_logs: List[Dict[str, Any]] = []
        self._filtered_logs: List[Dict[str, Any]] = []

        self.current_page = 1
        self.total_pages = 1

        self._build_ui()
        self.refresh()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(14)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("Activity Logs")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search method, user, target, details...")
        self.search.setFixedWidth(360)
        self.search.textChanged.connect(self._apply_all_filters)
        hdr.addWidget(self.search)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        hdr.addWidget(self.btn_refresh)

        self.btn_export = QPushButton("Export CSV")
        self.btn_export.setObjectName("secondaryBtn")
        self.btn_export.clicked.connect(self.export_csv)
        hdr.addWidget(self.btn_export)

        root.addLayout(hdr)

        # Card container
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)

        subtitle = QLabel("System-wide audit logs (Admin)")
        subtitle.setObjectName("muted")
        card_layout.addWidget(subtitle)

        # Filter row (methods)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        filter_lbl = QLabel("Method Filter:")
        filter_lbl.setObjectName("muted")
        filter_row.addWidget(filter_lbl)

        self.cb_get = QCheckBox("GET")
        self.cb_post = QCheckBox("POST")
        self.cb_patch = QCheckBox("PATCH")
        self.cb_put = QCheckBox("PUT")
        self.cb_delete = QCheckBox("DELETE")
        self.cb_desktop = QCheckBox("DESKTOP")

        for cb in (self.cb_get, self.cb_post, self.cb_patch, self.cb_put, self.cb_delete, self.cb_desktop):
            cb.setChecked(True)
            cb.stateChanged.connect(self._apply_all_filters)
            filter_row.addWidget(cb)

        filter_row.addStretch()
        card_layout.addLayout(filter_row)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Method", "Target", "Source", "User ID", "User Name", "Timestamp", "Details"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Fix spacing / readability
        try:
            hh = self.table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Method
            hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Target
            hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Source
            hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # User ID
            hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # User Name
            hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Timestamp
            hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)           # Details
        except Exception:
            pass

        # ✅ Fill vertical space cleanly
        try:
            vh = self.table.verticalHeader()
            vh.setVisible(False)
            vh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass

        card_layout.addWidget(self.table, 1)

        # Pagination bar
        pag_row = QHBoxLayout()
        pag_row.setSpacing(6)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedWidth(28)
        self.btn_prev.clicked.connect(self._prev_page)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedWidth(28)
        self.btn_next.clicked.connect(self._next_page)

        self.page_label = QLabel("Page 1 / 1")
        self.page_label.setObjectName("muted")

        pag_row.addWidget(self.btn_prev)
        pag_row.addWidget(self.btn_next)
        pag_row.addSpacing(10)
        pag_row.addWidget(self.page_label)
        pag_row.addStretch()

        card_layout.addLayout(pag_row)

        root.addWidget(card, 1)

    # ---------------------------------------------------------
    # Data fetch
    # ---------------------------------------------------------
    def refresh(self):
        if self.role != "admin":
            self._all_logs = []
            self._filtered_logs = []
            self.current_page = 1
            self.total_pages = 1
            self._render_page()
            return

        try:
            logs = self._fetch_admin_logs(limit=500)
            self._all_logs = logs
            self.current_page = 1
            self._apply_all_filters()
        except Exception:
            print("\n>>> ACTIVITY PAGE FETCH ERROR <<<")
            traceback.print_exc()
            self._all_logs = []
            self._filtered_logs = []
            self.current_page = 1
            self.total_pages = 1
            self._render_page()

    def _fetch_admin_logs(self, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Try multiple API shapes:
        - get_api_logs(limit=?)
        - get_activity_logs(limit=?)
        - get_logs(limit=?)
        - get_user_logs(admin_id, limit=?)
        """
        fn = getattr(self.api, "get_api_logs", None)
        if callable(fn):
            res = self._safe_call_with_limit(fn, limit)
            logs = self._extract_logs(res)
            if logs:
                return logs

        fn = getattr(self.api, "get_activity_logs", None)
        if callable(fn):
            res = self._safe_call_with_limit(fn, limit)
            logs = self._extract_logs(res)
            if logs:
                return logs

        fn = getattr(self.api, "get_logs", None)
        if callable(fn):
            res = self._safe_call_with_limit(fn, limit)
            logs = self._extract_logs(res)
            if logs:
                return logs

        fn = getattr(self.api, "get_user_logs", None)
        if callable(fn):
            admin_id = self.user.get("id", 0)
            try:
                res = fn(admin_id, limit=limit)
            except TypeError:
                res = fn(admin_id, limit)
            logs = self._extract_logs(res)
            if logs:
                return logs

        return []

    def _safe_call_with_limit(self, fn, limit: int):
        try:
            return fn(limit=limit)
        except TypeError:
            pass
        try:
            return fn(limit)
        except TypeError:
            pass
        return fn()

    def _extract_logs(self, res) -> List[Dict[str, Any]]:
        if res is None:
            return []
        if isinstance(res, list):
            return res
        if isinstance(res, dict):
            for key in (
                "logs", "activities", "activity_logs",
                "api_activity_logs", "data", "items", "results"
            ):
                val = res.get(key)
                if isinstance(val, list):
                    return val
        return []

    # ---------------------------------------------------------
    # Filtering (method + search)
    # ---------------------------------------------------------
    def _apply_all_filters(self):
        logs = self._all_logs or []

        allowed = set()
        if self.cb_get.isChecked():
            allowed.add("GET")
        if self.cb_post.isChecked():
            allowed.add("POST")
        if self.cb_patch.isChecked():
            allowed.add("PATCH")
        if self.cb_put.isChecked():
            allowed.add("PUT")
        if self.cb_delete.isChecked():
            allowed.add("DELETE")
        if self.cb_desktop.isChecked():
            allowed.add("DESKTOP")

        if allowed:
            logs = [
                l for l in logs
                if str(l.get("method") or "").upper() in allowed
            ]
        else:
            logs = []

        q = (self.search.text() or "").strip().lower()
        if q:
            def blob(log: Dict[str, Any]) -> str:
                return " ".join([
                    str(log.get("method", "")),
                    str(log.get("target", "")),
                    str(log.get("target_entity", "")),
                    str(log.get("source", "")),
                    str(log.get("user_id", "")),
                    str(log.get("user_name", "")),
                    str(log.get("username", "")),
                    str(log.get("details", "")),
                    str(log.get("timestamp", "")),
                    str(log.get("log_time", "")),
                ]).lower()
            logs = [l for l in logs if q in blob(l)]

        self._filtered_logs = logs

        total = len(self._filtered_logs)
        self.total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        if self.current_page < 1:
            self.current_page = 1

        self._render_page()

    # ---------------------------------------------------------
    # Rendering
    # ---------------------------------------------------------
    def _render_page(self):
        logs = self._filtered_logs or []
        start = (self.current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_logs = logs[start:end]

        self.table.setRowCount(self.PAGE_SIZE)

        for i in range(self.PAGE_SIZE):
            if i < len(page_logs):
                log = page_logs[i]

                method = str(log.get("method") or "").upper()
                target = str(log.get("target") or log.get("target_entity") or "")
                source = str(log.get("source") or "API")
                user_id = str(log.get("user_id") or "")
                user_name = str(
                    log.get("user_name")
                    or log.get("username")
                    or log.get("full_name")
                    or "System"
                )
                timestamp = str(log.get("timestamp") or log.get("log_time") or "")
                details = str(log.get("details") or "")

                vals = [method, target, source, user_id, user_name, timestamp, details]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(str(v))
                    it.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    self.table.setItem(i, c, it)
            else:
                for c in range(7):
                    blank = QTableWidgetItem("")
                    blank.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.table.setItem(i, c, blank)

        try:
            self.table.resizeColumnsToContents()
        except Exception:
            pass

        self.page_label.setText(f"Page {self.current_page} / {self.total_pages}")
        self.btn_prev.setDisabled(self.current_page <= 1)
        self.btn_next.setDisabled(self.current_page >= self.total_pages)

    # ---------------------------------------------------------
    # Pagination actions
    # ---------------------------------------------------------
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_page()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._render_page()

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------
    def export_csv(self):
        if self.role != "admin":
            QMessageBox.information(self, "Export", "Only admins can export logs.")
            return

        if not self._filtered_logs:
            QMessageBox.information(self, "Export", "No logs available to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Activity Logs",
            "activity_logs.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=[
                        "method", "target", "source",
                        "user_id", "user_name", "timestamp", "details"
                    ]
                )
                w.writeheader()

                for log in self._filtered_logs:
                    w.writerow({
                        "method": log.get("method", ""),
                        "target": log.get("target") or log.get("target_entity") or "",
                        "source": log.get("source", "API"),
                        "user_id": log.get("user_id", ""),
                        "user_name": log.get("user_name") or log.get("username") or "",
                        "timestamp": log.get("timestamp") or log.get("log_time") or "",
                        "details": log.get("details", ""),
                    })

            QMessageBox.information(self, "Export", f"CSV saved:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
