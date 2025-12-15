# desktop_app/ui/reports/reports_page.py

from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Dict, Any, Tuple, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QFrame, QSizePolicy, QMessageBox,
    QFileDialog, QDateEdit, QSpinBox
)
from PyQt6.QtCore import Qt, QDate

from desktop_app.services.report_generator import (
    DesktopReportGenerator,
    REPORT_SPECS,  # kept for compatibility
    ReportSpec
)


class ReportsPage(QWidget):
    """
    Reports UI (Desktop)

    Improved filter UX:
      - One "Period" dropdown for date-based reports:
          Today, Yesterday, Last 7, Last 30, This month,
          Specific day..., Custom range...
      - Specific day = start_date == end_date (same-day checks supported)
      - Custom range allows same-day too (start == end is allowed)
      - UI displays dd/MM/yy but sends YYYY-MM-DD to backend.
    """

    PERIOD_TODAY = "Today"
    PERIOD_YESTERDAY = "Yesterday"
    PERIOD_LAST_7 = "Last 7 days"
    PERIOD_LAST_30 = "Last 30 days"
    PERIOD_THIS_MONTH = "This month"
    PERIOD_SPECIFIC_DAY = "Specific day…"
    PERIOD_CUSTOM_RANGE = "Custom range…"

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)

        self.user = user_data or {}
        self.role = (self.user.get("role") or "").lower()

        self.kpi_value_labels: Dict[str, QLabel] = {}
        self.label_to_key: Dict[str, str] = {}
        self.current_spec: Optional[ReportSpec] = None

        self.init_ui()

    # ---------------------------------------------------------
    # UI setup
    # ---------------------------------------------------------
    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(16)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("Reports")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        # Report type dropdown
        self.report_type = QComboBox()
        self._populate_report_types()
        self.report_type.setFixedWidth(320)
        self.report_type.currentTextChanged.connect(self.on_report_type_changed)
        hdr.addWidget(self.report_type)

        self.btn_generate = QPushButton("Generate")
        self.btn_generate.setObjectName("primaryBtn")
        self.btn_generate.setFixedHeight(36)
        self.btn_generate.clicked.connect(self.on_generate_clicked)
        hdr.addWidget(self.btn_generate)

        self.btn_pdf = QPushButton("Download PDF")
        self.btn_pdf.setFixedHeight(36)
        self.btn_pdf.clicked.connect(self.on_download_pdf_clicked)
        hdr.addWidget(self.btn_pdf)

        root.addLayout(hdr)

        # Filters card
        self.filters_card = QFrame()
        self.filters_card.setObjectName("Card")
        self.filters_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        fl = QHBoxLayout(self.filters_card)
        fl.setContentsMargins(12, 10, 12, 10)
        fl.setSpacing(12)

        filters_title = QLabel("Filters")
        filters_title.setObjectName("CardTitle")
        fl.addWidget(filters_title)

        # ---- Period dropdown (date-range reports)
        self.period_label = QLabel("Period:")
        self.period_label.setObjectName("mutedLabel")
        fl.addWidget(self.period_label)

        self.period = QComboBox()
        self.period.setFixedWidth(170)
        self.period.addItems([
            self.PERIOD_TODAY,
            self.PERIOD_YESTERDAY,
            self.PERIOD_LAST_7,
            self.PERIOD_LAST_30,
            self.PERIOD_THIS_MONTH,
            self.PERIOD_SPECIFIC_DAY,
            self.PERIOD_CUSTOM_RANGE
        ])
        self.period.currentTextChanged.connect(self.on_period_changed)
        fl.addWidget(self.period)

        # ---- Specific day picker (shown only for "Specific day…")
        self.day_label = QLabel("Date:")
        self.day_label.setObjectName("mutedLabel")
        fl.addWidget(self.day_label)

        self.day_date = QDateEdit()
        self.day_date.setCalendarPopup(True)
        self.day_date.setDisplayFormat("dd/MM/yy")  # friendly UI
        self.day_date.setFixedWidth(110)
        fl.addWidget(self.day_date)

        # ---- Range pickers (shown only for "Custom range…")
        self.start_label = QLabel("Start:")
        self.start_label.setObjectName("mutedLabel")
        fl.addWidget(self.start_label)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yy")  # friendly UI
        self.start_date.setFixedWidth(110)
        fl.addWidget(self.start_date)

        self.end_label = QLabel("End:")
        self.end_label.setObjectName("mutedLabel")
        fl.addWidget(self.end_label)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd/MM/yy")  # friendly UI
        self.end_date.setFixedWidth(110)
        fl.addWidget(self.end_date)

        # ---- Days ahead (alerts report)
        self.days_ahead_label = QLabel("Days ahead:")
        self.days_ahead_label.setObjectName("mutedLabel")
        fl.addWidget(self.days_ahead_label)

        self.days_ahead = QSpinBox()
        self.days_ahead.setRange(1, 365)
        self.days_ahead.setValue(7)
        self.days_ahead.setFixedWidth(80)
        fl.addWidget(self.days_ahead)

        fl.addStretch()
        root.addWidget(self.filters_card)

        # KPI row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        kpi_row.addWidget(self.make_kpi("Revenue (30d)", "₱0.00", key="revenue_30d"))
        kpi_row.addWidget(self.make_kpi("Avg Order (30d)", "₱0.00", key="avg_order_30d"))
        kpi_row.addWidget(self.make_kpi("Top Category", "N/A", key="top_category"))
        kpi_row.addWidget(self.make_kpi("Alerts (7d)", "0", key="alerts_7d"))
        root.addLayout(kpi_row)

        # Report output
        self.report_area = QFrame()
        self.report_area.setObjectName("Card")
        self.report_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        rl = QVBoxLayout(self.report_area)
        rl.setContentsMargins(12, 12, 12, 12)
        rl.setSpacing(10)

        header = QLabel("Report Output")
        header.setObjectName("CardTitle")
        rl.addWidget(header)

        self.notes = QTextEdit()
        self.notes.setReadOnly(True)
        self.notes.setPlaceholderText("Generated report data will appear here.")
        rl.addWidget(self.notes, 1)

        root.addWidget(self.report_area, 1)

        # Set initial dates
        today = date.today()
        self._set_qdate(self.day_date, today)
        self._set_qdate(self.start_date, today - timedelta(days=30))
        self._set_qdate(self.end_date, today)

        # Initial KPI refresh
        self.refresh_kpis_safely()

        # Init visibility based on selected report
        self.on_report_type_changed(self.report_type.currentText())

        if self.report_type.count() == 0:
            self.notes.setPlainText(
                "No report specs were found.\n"
                "Check DesktopReportGenerator.list_reports() and REPORT_SPECS."
            )

    def _populate_report_types(self):
        self.report_type.clear()
        self.label_to_key.clear()

        try:
            specs = DesktopReportGenerator.list_reports()
        except Exception:
            specs = []

        try:
            specs = sorted(specs, key=lambda s: (s.label or "").lower())
        except Exception:
            pass

        for spec in specs:
            try:
                self.report_type.addItem(spec.label)
                self.label_to_key[spec.label] = spec.key
            except Exception:
                continue

    def make_kpi(self, title_text: str, value_text: str, key: str):
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 12, 14, 12)
        inner.setSpacing(2)

        label = QLabel(title_text)
        label.setObjectName("CardTitle")

        value = QLabel(value_text)
        value.setObjectName("CardValue")
        value.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.kpi_value_labels[key] = value

        inner.addWidget(label)
        inner.addWidget(value)
        return card

    # ---------------------------------------------------------
    # Small helpers
    # ---------------------------------------------------------
    def show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def show_info(self, title: str, message: str):
        QMessageBox.information(self, title, message)

    def peso(self, value: Any) -> str:
        try:
            return f"₱{float(value):,.2f}"
        except Exception:
            return "₱0.00"

    def _safe_get(self, obj: Dict[str, Any], key: str, default=None):
        try:
            return obj.get(key, default)
        except Exception:
            return default

    def _set_qdate(self, widget: QDateEdit, d: date):
        widget.setDate(QDate(d.year, d.month, d.day))

    def _qdate_to_iso(self, qd: QDate) -> str:
        # Backend expects YYYY-MM-DD
        return qd.toString("yyyy-MM-dd")

    # ---------------------------------------------------------
    # Filter UX logic
    # ---------------------------------------------------------
    def on_report_type_changed(self, label: str):
        key = self.label_to_key.get((label or "").strip())
        if not key:
            self.current_spec = None
            self._set_filters_visible(False, False)
            return

        try:
            spec = DesktopReportGenerator.get_spec(key)
        except Exception:
            self.current_spec = None
            self._set_filters_visible(False, False)
            return

        self.current_spec = spec
        needs_date = bool(getattr(spec, "needs_date_range", False))
        needs_days = bool(getattr(spec, "needs_days_ahead", False))

        self._set_filters_visible(needs_date, needs_days)

        # Update date controls visibility based on period selection
        if needs_date:
            self.on_period_changed(self.period.currentText())

    def _set_filters_visible(self, show_date_range: bool, show_days_ahead: bool):
        self.filters_card.setVisible(show_date_range or show_days_ahead)

        # Date-related widgets (period + pickers)
        self.period_label.setVisible(show_date_range)
        self.period.setVisible(show_date_range)

        # specific day widgets
        self.day_label.setVisible(False)
        self.day_date.setVisible(False)

        # range widgets
        self.start_label.setVisible(False)
        self.start_date.setVisible(False)
        self.end_label.setVisible(False)
        self.end_date.setVisible(False)

        # Days ahead widgets
        self.days_ahead_label.setVisible(show_days_ahead)
        self.days_ahead.setVisible(show_days_ahead)

    def on_period_changed(self, period: str):
        # Only applies to date-range reports
        if not self.current_spec or not getattr(self.current_spec, "needs_date_range", False):
            return

        today = date.today()

        # Hide all date pickers first
        self.day_label.setVisible(False)
        self.day_date.setVisible(False)
        self.start_label.setVisible(False)
        self.start_date.setVisible(False)
        self.end_label.setVisible(False)
        self.end_date.setVisible(False)

        if period == self.PERIOD_TODAY:
            self._set_qdate(self.day_date, today)

        elif period == self.PERIOD_YESTERDAY:
            self._set_qdate(self.day_date, today - timedelta(days=1))

        elif period == self.PERIOD_LAST_7:
            self._set_qdate(self.start_date, today - timedelta(days=7))
            self._set_qdate(self.end_date, today)

        elif period == self.PERIOD_LAST_30:
            self._set_qdate(self.start_date, today - timedelta(days=30))
            self._set_qdate(self.end_date, today)

        elif period == self.PERIOD_THIS_MONTH:
            start = today.replace(day=1)
            self._set_qdate(self.start_date, start)
            self._set_qdate(self.end_date, today)

        elif period == self.PERIOD_SPECIFIC_DAY:
            # Show single date picker (start=end)
            self.day_label.setVisible(True)
            self.day_date.setVisible(True)

            # default: today
            self._set_qdate(self.day_date, today)

        elif period == self.PERIOD_CUSTOM_RANGE:
            # Show start/end pickers (same-day allowed)
            self.start_label.setVisible(True)
            self.start_date.setVisible(True)
            self.end_label.setVisible(True)
            self.end_date.setVisible(True)

            # default: last 30 days
            self._set_qdate(self.start_date, today - timedelta(days=30))
            self._set_qdate(self.end_date, today)

        # For non-custom presets that use ranges, show nothing (clean UI)
        # But when generating, we still compute correct params.

    def _collect_params_for_spec(self, spec: ReportSpec) -> Dict[str, Any]:
        params: Dict[str, Any] = {}

        if getattr(spec, "needs_date_range", False):
            period = self.period.currentText().strip()
            today = date.today()

            if period == self.PERIOD_TODAY:
                start = end = today

            elif period == self.PERIOD_YESTERDAY:
                start = end = today - timedelta(days=1)

            elif period == self.PERIOD_LAST_7:
                start, end = today - timedelta(days=7), today

            elif period == self.PERIOD_LAST_30:
                start, end = today - timedelta(days=30), today

            elif period == self.PERIOD_THIS_MONTH:
                start, end = today.replace(day=1), today

            elif period == self.PERIOD_SPECIFIC_DAY:
                qd = self.day_date.date()
                start = end = date(qd.year(), qd.month(), qd.day())

            elif period == self.PERIOD_CUSTOM_RANGE:
                s = self.start_date.date()
                e = self.end_date.date()
                start = date(s.year(), s.month(), s.day())
                end = date(e.year(), e.month(), e.day())
            else:
                start, end = today - timedelta(days=30), today

            # Allow same day checks ✅ (start == end is OK)
            if start > end:
                raise ValueError("Start date cannot be after end date.")

            params["start_date"] = start.isoformat()
            params["end_date"] = end.isoformat()

        if getattr(spec, "needs_days_ahead", False):
            params["days_ahead"] = int(self.days_ahead.value())

        return params

    # ---------------------------------------------------------
    # KPI refresh
    # ---------------------------------------------------------
    def refresh_kpis_safely(self):
        # Defaults
        self.kpi_value_labels.get("revenue_30d", QLabel()).setText("₱0.00")
        self.kpi_value_labels.get("avg_order_30d", QLabel()).setText("₱0.00")
        self.kpi_value_labels.get("top_category", QLabel()).setText("N/A")
        self.kpi_value_labels.get("alerts_7d", QLabel()).setText("0")

        # Revenue + Avg Order (last 30 days)
        try:
            today = date.today()
            start = (today - timedelta(days=30)).isoformat()
            end = today.isoformat()

            sp = DesktopReportGenerator.generate_report(
                "sales_performance",
                start_date=start,
                end_date=end
            )
            summary = self._safe_get(sp, "summary", {}) or {}
            total_income = self._safe_get(summary, "total_income", 0) or 0
            total_tx = self._safe_get(summary, "total_transactions", 0) or 0

            if "revenue_30d" in self.kpi_value_labels:
                self.kpi_value_labels["revenue_30d"].setText(self.peso(total_income))

            avg = (float(total_income) / float(total_tx)) if float(total_tx) > 0 else 0
            if "avg_order_30d" in self.kpi_value_labels:
                self.kpi_value_labels["avg_order_30d"].setText(self.peso(avg))
        except Exception:
            pass

        # Top Category
        try:
            cd = DesktopReportGenerator.generate_report("category_distribution")
            categories = self._safe_get(cd, "categories", []) or []
            if categories:
                categories_sorted = sorted(
                    categories,
                    key=lambda c: (
                        float(c.get("percentage_share", 0) or 0),
                        int(c.get("total_stock_quantity", 0) or 0)
                    ),
                    reverse=True
                )
                top = categories_sorted[0]
                if "top_category" in self.kpi_value_labels:
                    self.kpi_value_labels["top_category"].setText(top.get("category_name", "N/A"))
        except Exception:
            pass

        # Alerts count (7d)
        try:
            ar = DesktopReportGenerator.generate_report("alerts", days_ahead=7)
            summary = self._safe_get(ar, "summary", {}) or {}
            total_alerts = self._safe_get(summary, "total_alerts", 0) or 0
            if "alerts_7d" in self.kpi_value_labels:
                self.kpi_value_labels["alerts_7d"].setText(str(total_alerts))
        except Exception:
            pass

    # ---------------------------------------------------------
    # Generate button
    # ---------------------------------------------------------
    def on_generate_clicked(self):
        label = self.report_type.currentText().strip()
        key = self.label_to_key.get(label)

        if not key:
            self.notes.setPlainText("Unknown report type selected.")
            return

        self.refresh_kpis_safely()

        try:
            spec = DesktopReportGenerator.get_spec(key)
            params = self._collect_params_for_spec(spec)
            data = DesktopReportGenerator.generate_report(spec.key, **params)
            self._render_report(spec, data, params=params)
        except Exception as e:
            self.show_error("Report Error", str(e))

    # ---------------------------------------------------------
    # Renderers
    # ---------------------------------------------------------
    def _render_report(self, spec: ReportSpec, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None):
        key = spec.key
        params = params or {}

        if key == "sales_performance":
            self._render_sales_performance(data)
        elif key == "category_distribution":
            self._render_category_distribution(data)
        elif key == "retailer_performance":
            self._render_retailer_performance(data)
        elif key == "alerts":
            self._render_alerts(data, days_ahead=params.get("days_ahead"))
        elif key == "transactions":
            self._render_transactions(data)
        elif key == "user_accounts":
            self._render_user_accounts(data)
        elif key == "managerial_activity":
            self._render_managerial_activity(data)
        else:
            import json
            try:
                self.notes.setPlainText(json.dumps(data, indent=2))
            except Exception:
                self.notes.setPlainText(str(data))

    def _render_sales_performance(self, data: Dict[str, Any]):
        summary = data.get("summary", {}) or {}
        sales = data.get("sales", []) or []
        dr = data.get("date_range", {}) or {}

        lines = [
            "SALES PERFORMANCE REPORT",
            f"Period: {dr.get('start')} to {dr.get('end')}",
            "",
            "SUMMARY",
            f"- Total Income: {self.peso(summary.get('total_income', 0))}",
            f"- Total Quantity Sold: {summary.get('total_quantity_sold', 0)}",
            f"- Total Transactions: {summary.get('total_transactions', 0)}",
            "",
            "RECENT SALES (top 20 lines)",
            "-" * 48
        ]

        for row in sales[:20]:
            lines.append(
                f"Sale #{row.get('sale_id')} | {row.get('product_name')} "
                f"x{row.get('quantity_sold')} | {self.peso(row.get('total_price', 0))} "
                f"| {row.get('retailer_name')}"
            )

        if not sales:
            lines.append("No sales found for this period.")

        self.notes.setPlainText("\n".join(lines))

    def _render_category_distribution(self, data: Dict[str, Any]):
        summary = data.get("summary", {}) or {}
        categories = data.get("categories", []) or []

        lines = [
            "CATEGORY DISTRIBUTION REPORT",
            "",
            "SUMMARY",
            f"- Total Categories: {summary.get('total_categories', 0)}",
            f"- Total Stock: {summary.get('total_stock', 0)}",
            "",
            "BREAKDOWN",
            "-" * 48
        ]

        for c in categories:
            lines.append(
                f"{c.get('category_name')} | "
                f"Products: {c.get('number_of_products', 0)} | "
                f"Stock: {c.get('total_stock_quantity', 0)} | "
                f"Share: {c.get('percentage_share', 0)}%"
            )

        if not categories:
            lines.append("No categories found.")

        self.notes.setPlainText("\n".join(lines))

    def _render_retailer_performance(self, data: Dict[str, Any]):
        summary = data.get("summary", {}) or {}
        retailers = data.get("retailers", []) or []

        lines = [
            "RETAILER PERFORMANCE REPORT",
            "",
            "SUMMARY",
            f"- Total Retailers: {summary.get('total_retailers', 0)}",
            f"- Active Today: {summary.get('active_today', 0)}",
            "",
            "LEADERBOARD (top 10)",
            "-" * 48
        ]

        for r in retailers[:10]:
            lines.append(
                f"{r.get('retailer_name')} | "
                f"Streak: {r.get('streak_count', 0)} | "
                f"Today: {self.peso(r.get('current_sales', 0))} | "
                f"Quota: {self.peso(r.get('daily_quota', 0))} | "
                f"Progress: {r.get('quota_progress', 0)}%"
            )

        if not retailers:
            lines.append("No retailer metrics found yet.")

        self.notes.setPlainText("\n".join(lines))

    def _render_alerts(self, data: Dict[str, Any], days_ahead: Optional[int] = None):
        summary = data.get("summary", {}) or {}
        alerts = data.get("alerts", []) or []
        window = int(days_ahead) if days_ahead is not None else 7

        lines = [
            "LOW-STOCK & EXPIRATION ALERTS",
            f"Window: next {window} day(s)",
            "",
            "SUMMARY",
            f"- Total Alerts: {summary.get('total_alerts', 0)}",
            f"- Critical: {summary.get('critical_alerts', 0)}",
            f"- Warning: {summary.get('warning_alerts', 0)}",
            "",
            "ALERT DETAILS",
            "-" * 48
        ]

        for a in alerts[:30]:
            lines.append(
                f"{a.get('product_name')} | "
                f"Stock: {a.get('current_stock')} (min {a.get('min_stock_level')}) | "
                f"Expiry: {a.get('expiration_date') or 'N/A'} | "
                f"{a.get('alert_status')} | {a.get('severity')}"
            )

        if not alerts:
            lines.append("No alerts detected.")

        self.notes.setPlainText("\n".join(lines))

    def _render_transactions(self, data: Dict[str, Any]):
        summary = data.get("summary", {}) or {}
        tx = data.get("transactions", []) or []
        dr = data.get("date_range", {}) or {}

        lines = [
            "DETAILED SALES TRANSACTIONS REPORT",
            f"Period: {dr.get('start')} to {dr.get('end')}",
            "",
            "SUMMARY",
            f"- Total Transaction Lines: {summary.get('total_transactions', 0)}",
            f"- Total Sales Count: {summary.get('total_sales_count', 0)}",
            f"- Total Revenue: {self.peso(summary.get('total_revenue', 0))}",
            f"- Total Items Sold: {summary.get('total_items_sold', 0)}",
            "",
            "RECENT TRANSACTION LINES (top 20)",
            "-" * 48
        ]

        for t in tx[:20]:
            lines.append(
                f"Sale #{t.get('sale_id')} | {t.get('product_name')} "
                f"x{t.get('quantity_sold')} @ {self.peso(t.get('unit_price', 0))} "
                f"= {self.peso(t.get('line_total', 0))} | {t.get('retailer_name')}"
            )

        if not tx:
            lines.append("No transactions found.")

        self.notes.setPlainText("\n".join(lines))

    def _render_user_accounts(self, data: Dict[str, Any]):
        summary = data.get("summary", {}) or {}
        users = data.get("users", []) or []

        lines = [
            "USER ACCOUNTS REPORT",
            "",
            "SUMMARY",
            f"- Total Users: {summary.get('total_users', 0)}",
            f"- Admins: {summary.get('admins', 0)}",
            f"- Managers: {summary.get('managers', 0)}",
            f"- Retailers/Staff: {summary.get('retailers', 0)}",
            "",
            "USERS (top 30)",
            "-" * 48
        ]

        for u in users[:30]:
            lines.append(
                f"#{u.get('user_id')} | {u.get('username')} | "
                f"{u.get('full_name')} | {u.get('role')} | {u.get('account_status', 'Active')}"
            )

        if not users:
            lines.append("No users found.")

        self.notes.setPlainText("\n".join(lines))

    def _render_managerial_activity(self, data: Dict[str, Any]):
        summary = data.get("summary", {}) or {}
        logs = data.get("logs", []) or []
        dr = data.get("date_range", {}) or {}

        lines = [
            "MANAGERIAL ACTIVITY LOG",
            f"Period: {dr.get('start')} to {dr.get('end')}",
            "",
            "SUMMARY",
            f"- Total Actions: {summary.get('total_actions', len(logs))}",
            f"- Unique Managers: {summary.get('unique_managers', 0)}",
            "",
            "RECENT ACTIVITIES (top 30)",
            "-" * 48
        ]

        for log in logs[:30]:
            lines.append(
                f"{log.get('date_time', '')} | {log.get('action_performed', '')} | "
                f"{log.get('product_name', '')} | {log.get('manager_name', '')} | "
                f"{log.get('notes', '')}"
            )

        if not logs:
            lines.append("No activity logs found.")

        self.notes.setPlainText("\n".join(lines))

    # ---------------------------------------------------------
    # PDF download
    # ---------------------------------------------------------
    def on_download_pdf_clicked(self):
        label = self.report_type.currentText().strip()
        key = self.label_to_key.get(label)

        if not key:
            self.show_error("PDF Error", "Unknown report type selected.")
            return

        try:
            spec = DesktopReportGenerator.get_spec(key)
            params = self._collect_params_for_spec(spec)
            content = DesktopReportGenerator.download_pdf(key, **params)
        except Exception as e:
            self.show_error("PDF Download Error", str(e))
            return

        if not content:
            self.show_error("PDF Download Error", "Empty PDF content received.")
            return

        default_name = f"{spec.key}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Report",
            default_name,
            "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "wb") as f:
                f.write(content)
            self.show_info("PDF Saved", f"Report saved successfully:\n{file_path}")
        except Exception as e:
            self.show_error("Save Error", f"Failed to save PDF:\n{str(e)}")
