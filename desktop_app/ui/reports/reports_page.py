# desktop_app/ui/reports/reports_page.py

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QFrame, QSizePolicy, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt

from desktop_app.services.report_generator import (
    DesktopReportGenerator,
    REPORT_SPECS,  # kept in case you reference it elsewhere
    ReportSpec
)


class ReportsPage(QWidget):
    """
    Reports UI (Desktop)

    Works with:
      - DesktopReportGenerator
      - REPORT_SPECS

    Features:
      - Real KPI fetch
      - Real JSON report generation
      - PDF download via generator
      - Resilient UI (won't crash if some endpoints aren't ready)

    IMPORTANT:
      This page is instantiated by MainWindow's dynamic loader which may call:
        - ReportsPage(self.user)
        - ReportsPage(user_data=self.user)

      So we must accept user_data and not treat the dict as QWidget parent.
    """

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)

        self.user = user_data or {}
        self.role = (self.user.get("role") or "").lower()

        # Store KPI value labels so we can update them
        self.kpi_value_labels: Dict[str, QLabel] = {}

        # Map dropdown label -> report key
        self.label_to_key: Dict[str, str] = {}

        self.init_ui()

    # ---------------------------------------------------------
    # UI setup
    # ---------------------------------------------------------
    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(20)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("Reports")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        # Report type dropdown (dynamic)
        self.report_type = QComboBox()
        self._populate_report_types()
        self.report_type.setFixedWidth(280)
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

        # KPI row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        kpi_row.addWidget(self.make_kpi("Revenue (30d)", "₱0.00", key="revenue_30d"))
        kpi_row.addWidget(self.make_kpi("Avg Order (30d)", "₱0.00", key="avg_order_30d"))
        kpi_row.addWidget(self.make_kpi("Top Category", "N/A", key="top_category"))
        kpi_row.addWidget(self.make_kpi("Alerts (7d)", "0", key="alerts_7d"))

        root.addLayout(kpi_row)

        # Report output area
        self.report_area = QFrame()
        self.report_area.setObjectName("Card")
        self.report_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        report_layout = QVBoxLayout(self.report_area)
        report_layout.setContentsMargins(12, 12, 12, 12)
        report_layout.setSpacing(10)

        header = QLabel("Report Output")
        header.setObjectName("CardTitle")
        report_layout.addWidget(header)

        self.notes = QTextEdit()
        self.notes.setReadOnly(True)
        self.notes.setPlaceholderText("Generated report data will appear here.")
        report_layout.addWidget(self.notes, 1)

        root.addWidget(self.report_area, 1)

        # Initial KPI refresh
        self.refresh_kpis_safely()

        # Friendly default content
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

        # Optional: sort by label for nicer UX
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
    # Helpers
    # ---------------------------------------------------------
    def last_30_days_range(self) -> Tuple[str, str]:
        today = datetime.now().date()
        start = today - timedelta(days=30)
        return start.isoformat(), today.isoformat()

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

    # ---------------------------------------------------------
    # KPI refresh
    # ---------------------------------------------------------
    def refresh_kpis_safely(self):
        # Defaults
        if "revenue_30d" in self.kpi_value_labels:
            self.kpi_value_labels["revenue_30d"].setText("₱0.00")
        if "avg_order_30d" in self.kpi_value_labels:
            self.kpi_value_labels["avg_order_30d"].setText("₱0.00")
        if "top_category" in self.kpi_value_labels:
            self.kpi_value_labels["top_category"].setText("N/A")
        if "alerts_7d" in self.kpi_value_labels:
            self.kpi_value_labels["alerts_7d"].setText("0")

        # 1) Revenue + Avg Order from sales performance (last 30 days)
        try:
            start, end = self.last_30_days_range()
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

            try:
                avg = float(total_income) / float(total_tx) if float(total_tx) > 0 else 0
            except Exception:
                avg = 0

            if "avg_order_30d" in self.kpi_value_labels:
                self.kpi_value_labels["avg_order_30d"].setText(self.peso(avg))
        except Exception:
            pass

        # 2) Top Category from category distribution
        try:
            cd = DesktopReportGenerator.generate_report("category_distribution")
            categories = self._safe_get(cd, "categories", []) or []
            if categories:
                try:
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
                    if "top_category" in self.kpi_value_labels:
                        self.kpi_value_labels["top_category"].setText("N/A")
        except Exception:
            pass

        # 3) Alerts count (7 days)
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

        # Always refresh KPIs when generating
        self.refresh_kpis_safely()

        try:
            spec = DesktopReportGenerator.get_spec(key)
            data = self._generate_by_spec(spec)
            self._render_report(spec, data)
        except Exception as e:
            self.show_error("Report Error", str(e))

    def _generate_by_spec(self, spec: ReportSpec) -> Dict[str, Any]:
        params: Dict[str, Any] = {}

        if getattr(spec, "needs_date_range", False):
            start, end = self.last_30_days_range()
            params["start_date"] = start
            params["end_date"] = end

        if getattr(spec, "needs_days_ahead", False):
            params["days_ahead"] = 7

        return DesktopReportGenerator.generate_report(spec.key, **params)

    # ---------------------------------------------------------
    # Report renderers
    # ---------------------------------------------------------
    def _render_report(self, spec: ReportSpec, data: Dict[str, Any]):
        """
        Human-readable rendering based on known report shapes.
        Safely falls back to pretty-printed JSON if structure is unexpected.
        """
        key = spec.key

        if key == "sales_performance":
            self._render_sales_performance(data)
        elif key == "category_distribution":
            self._render_category_distribution(data)
        elif key == "retailer_performance":
            self._render_retailer_performance(data)
        elif key == "alerts":
            self._render_alerts(data)
        elif key == "transactions":
            self._render_transactions(data)
        elif key == "user_accounts":
            self._render_user_accounts(data)
        elif key == "managerial_activity":
            self._render_managerial_activity(data)
        else:
            # Generic fallback
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

    def _render_alerts(self, data: Dict[str, Any]):
        summary = data.get("summary", {}) or {}
        alerts = data.get("alerts", []) or []

        lines = [
            "LOW-STOCK & EXPIRATION ALERTS",
            "Window: next 7 days",
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
            f"- Total Activities: {summary.get('total_activities', len(logs))}",
            "",
            "RECENT ACTIVITIES (top 30)",
            "-" * 48
        ]

        for log in logs[:30]:
            lines.append(
                f"{log.get('timestamp', '')} | {log.get('action', '')} | "
                f"{log.get('entity', '')} | {log.get('details', '')}"
            )

        if not logs:
            lines.append("No activity logs found.")

        self.notes.setPlainText("\n".join(lines))

    # ---------------------------------------------------------
    # PDF download button
    # ---------------------------------------------------------
    def on_download_pdf_clicked(self):
        label = self.report_type.currentText().strip()
        key = self.label_to_key.get(label)

        if not key:
            self.show_error("PDF Error", "Unknown report type selected.")
            return

        try:
            spec = DesktopReportGenerator.get_spec(key)
        except Exception as e:
            self.show_error("PDF Error", str(e))
            return

        # Build params based on spec
        params: Dict[str, Any] = {}

        if getattr(spec, "needs_date_range", False):
            start, end = self.last_30_days_range()
            params["start_date"] = start
            params["end_date"] = end

        if getattr(spec, "needs_days_ahead", False):
            params["days_ahead"] = 7

        try:
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
