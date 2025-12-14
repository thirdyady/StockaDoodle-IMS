# desktop_app/ui/pages/alerts.py

from __future__ import annotations

from typing import Any, Dict, List

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QSizePolicy, QHeaderView
)

from desktop_app.services.report_generator import DesktopReportGenerator


class AlertsPage(QWidget):
    """
    Low-stock & expiration alerts (UI).

    Uses DesktopReportGenerator.generate_report("alerts", days_ahead=7)
    which returns a dict like:
    {
        "summary": {
            "total_alerts": int,
            "critical_alerts": int,
            "warning_alerts": int,
        },
        "alerts": [
            {
                "product_id": ...,
                "product_name": ...,
                "current_stock": ...,
                "min_stock_level": ...,
                "expiration_date": ...,
                "alert_status": ...,
                "severity": "critical" | "warning" | "info",
                "alert_type": "low_stock" | "expiration" | ...
            },
            ...
        ]
    }
    """

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}

        self._all_alerts: List[Dict[str, Any]] = []
        self._filtered_alerts: List[Dict[str, Any]] = []

        self._build_ui()
        self.refresh_alerts()

        # Optional: auto-refresh every 60s
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_alerts)
        self.timer.start(60_000)

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(14)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("Alerts")
        title.setObjectName("title")
        hdr.addWidget(title)

        subtitle = QLabel("Low Stock and Expiration alerts will be shown here.")
        subtitle.setObjectName("muted")
        hdr.addWidget(subtitle)
        hdr.addStretch()

        # Filter: severity
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["All severities", "Critical only", "Warning only"])
        self.severity_filter.currentIndexChanged.connect(self._apply_filters)
        hdr.addWidget(self.severity_filter)

        # Filter: type
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All types", "Low stock only", "Expiration only"])
        self.type_filter.currentIndexChanged.connect(self._apply_filters)
        hdr.addWidget(self.type_filter)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_alerts)
        hdr.addWidget(self.btn_refresh)

        root.addLayout(hdr)

        # KPI row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        total_card, self.lbl_total = self._make_kpi_card("Total Alerts", "0")
        critical_card, self.lbl_critical = self._make_kpi_card("Critical", "0")
        warning_card, self.lbl_warning = self._make_kpi_card("Warning", "0")

        kpi_row.addWidget(total_card)
        kpi_row.addWidget(critical_card)
        kpi_row.addWidget(warning_card)
        kpi_row.addStretch()

        root.addLayout(kpi_row)

        # Table card
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        subt = QLabel("Low stock and upcoming expirations (next 7 days)")
        subt.setObjectName("muted")
        card_layout.addWidget(subt)

        self.table = QTableWidget(0, 7)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.setHorizontalHeaderLabels([
            "Product",
            "Current Stock",
            "Min Level",
            "Expiration",
            "Status",
            "Severity",
            "Type",
        ])

        hh = self.table.horizontalHeader()
        try:
            hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)           # Product
            hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Current
            hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Min
            hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Expiration
            hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Status
            hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Sev
            hh.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Type
        except Exception:
            pass

        card_layout.addWidget(self.table, 1)
        root.addWidget(card, 1)

    def _make_kpi_card(self, title: str, value: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 10, 14, 8)
        inner.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("CardTitle")

        lbl_value = QLabel(value)
        lbl_value.setObjectName("CardValue")
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        inner.addWidget(lbl_title)
        inner.addWidget(lbl_value)

        # Return both the card to add to layouts, and the label for updating text
        return card, lbl_value

    # ---------------------------------------------------------
    # Data
    # ---------------------------------------------------------
    def refresh_alerts(self):
        """Fetch alerts report from the backend and refresh UI."""
        # reset KPIs
        self._set_kpis(0, 0, 0)
        self._all_alerts = []
        self._filtered_alerts = []

        try:
            data = DesktopReportGenerator.generate_report("alerts", days_ahead=7) or {}
        except Exception:
            # If backend not ready, show nothing but don't crash
            self._render_table([])
            return

        summary = data.get("summary", {}) or {}
        alerts = data.get("alerts", []) or []

        total = int(summary.get("total_alerts", len(alerts)) or 0)
        critical = int(summary.get("critical_alerts", 0) or 0)
        warning = int(summary.get("warning_alerts", 0) or 0)

        self._set_kpis(total, critical, warning)

        self._all_alerts = alerts
        self._apply_filters()

    def _set_kpis(self, total: int, critical: int, warning: int):
        self.lbl_total.setText(str(total))
        self.lbl_critical.setText(str(critical))
        self.lbl_warning.setText(str(warning))

    # ---------------------------------------------------------
    # Filtering + rendering
    # ---------------------------------------------------------
    def _apply_filters(self):
        alerts = self._all_alerts or []

        # Severity filter
        sev_idx = self.severity_filter.currentIndex() if hasattr(self, "severity_filter") else 0
        if sev_idx == 1:
            # Critical only
            alerts = [a for a in alerts if str(a.get("severity", "")).lower() == "critical"]
        elif sev_idx == 2:
            # Warning only
            alerts = [a for a in alerts if str(a.get("severity", "")).lower() == "warning"]

        # Type filter
        type_idx = self.type_filter.currentIndex() if hasattr(self, "type_filter") else 0
        if type_idx == 1:
            # Low stock only
            alerts = [a for a in alerts if str(a.get("alert_type", "")).lower() == "low_stock"]
        elif type_idx == 2:
            # Expiration only
            alerts = [a for a in alerts if str(a.get("alert_type", "")).lower() == "expiration"]

        self._filtered_alerts = alerts
        self._render_table(alerts)

    def _render_table(self, alerts: List[Dict[str, Any]]):
        self.table.setRowCount(0)

        def fmt(val: Any, default: str = "") -> str:
            # Only treat None as "missing" so that 0 stays "0"
            if val is None:
                return default
            return str(val)

        for alert in alerts:
            row = self.table.rowCount()
            self.table.insertRow(row)

            product_name = fmt(alert.get("product_name"), "")
            current_stock = fmt(alert.get("current_stock"), "0")
            min_level = fmt(alert.get("min_stock_level"), "0")
            expiration = fmt(alert.get("expiration_date"), "N/A")
            status = fmt(alert.get("alert_status"), "")
            severity = fmt(alert.get("severity"), "")
            alert_type = fmt(alert.get("alert_type"), "")

            values = [
                product_name,
                current_stock,
                min_level,
                expiration,
                status,
                severity,
                alert_type,
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                # Slightly emphasize critical rows
                if severity.lower() == "critical":
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(row, col, item)

        if not alerts:
            # Keep at least one empty row so UI doesn't look broken
            self.table.setRowCount(1)
            for c in range(self.table.columnCount()):
                it = QTableWidgetItem("")
                it.setFlags(Qt.ItemFlag.NoItemFlags)
                self.table.setItem(0, c, it)
