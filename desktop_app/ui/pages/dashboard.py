# desktop_app/ui/pages/dashboard.py

from __future__ import annotations

import traceback
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QGridLayout, QGraphicsDropShadowEffect, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QSizePolicy,
    QHeaderView, QProgressBar
)

from desktop_app.utils.api_wrapper import get_api


# ====================================
# Optional matplotlib embedding
# ====================================
MATPLOTLIB_OK = True
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
except Exception:
    MATPLOTLIB_OK = False
    FigureCanvas = None  # type: ignore
    Figure = None  # type: ignore


# ====================================
# Reusable shadows
# ====================================
def apply_card_shadow(widget):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(22)
    shadow.setOffset(0, 3)
    shadow.setColor(QColor(0, 0, 0, 90))
    widget.setGraphicsEffect(shadow)


# ====================================
# KPI Card Component
# ====================================
class DashboardCard(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("DashboardCard")

        self.setFixedHeight(135)
        self.setStyleSheet("""
            QFrame#DashboardCard {
                background: #FFFFFF;
                border-radius: 14px;
                border: 1px solid #DDE3EA;
            }
        """)

        apply_card_shadow(self)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(20, 16, 20, 16)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
            color: #4A5568;
            background: transparent;
        """)

        self.value_lbl = QLabel("--")
        self.value_lbl.setStyleSheet("""
            font-size: 28px;
            font-weight: 800;
            color: #1E3A8A;
            background: transparent;
        """)

        layout.addWidget(self.title_lbl)
        layout.addSpacing(8)
        layout.addWidget(self.value_lbl)
        layout.addStretch()

    def set_value(self, text):
        self.value_lbl.setText(str(text))


# ====================================
# Recent Activity Preview (Admin only)
# ====================================
class RecentActivityPreview(QFrame):
    view_more_clicked = pyqtSignal()

    PAGE_SIZE = 5
    MAX_LOGS = 10

    def __init__(self, user: Dict[str, Any], api):
        super().__init__()
        self.user = user or {}
        self.role = (self.user.get("role") or "").lower()
        self.api = api

        self._all_logs: List[Dict[str, Any]] = []
        self.current_page = 1

        self._build_ui()

    def _build_ui(self):
        self.setObjectName("activityFrame")
        self.setMinimumHeight(380)
        self.setStyleSheet("""
            #activityFrame {
                background: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #DDE3EA;
            }
        """)
        apply_card_shadow(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(12)

        header_row = QHBoxLayout()
        lbl_recent = QLabel("Recent Activity")
        lbl_recent.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            background: transparent;
        """)
        header_row.addWidget(lbl_recent)
        header_row.addStretch()

        self.btn_view_more = QPushButton("View More")
        self.btn_view_more.setObjectName("secondaryBtn")
        self.btn_view_more.setFixedHeight(30)
        self.btn_view_more.clicked.connect(self.view_more_clicked.emit)
        header_row.addWidget(self.btn_view_more)

        root.addLayout(header_row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["User", "Action", "Timestamp"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        try:
            hh = self.table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        except Exception:
            pass

        try:
            vh = self.table.verticalHeader()
            vh.setVisible(False)
            vh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass

        root.addWidget(self.table, 1)

        pag_row = QHBoxLayout()
        pag_row.setSpacing(6)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedWidth(28)
        self.btn_prev.clicked.connect(self._prev_page)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedWidth(28)
        self.btn_next.clicked.connect(self._next_page)

        self.page_label = QLabel("Page 1 / 2")
        self.page_label.setStyleSheet("color: rgba(0,0,0,0.55);")

        pag_row.addWidget(self.btn_prev)
        pag_row.addWidget(self.btn_next)
        pag_row.addSpacing(10)
        pag_row.addWidget(self.page_label)
        pag_row.addStretch()

        root.addLayout(pag_row)

    def refresh(self):
        self.current_page = 1
        self._all_logs = self._fetch_top_10()
        self._render_page()

    def _fetch_top_10(self) -> List[Dict[str, Any]]:
        logs: List[Dict[str, Any]] = []
        try:
            if self.role == "admin":
                res = self.api.get_api_logs(limit=self.MAX_LOGS)
                if isinstance(res, dict):
                    logs = res.get("logs", []) or []
                elif isinstance(res, list):
                    logs = res

            if not logs:
                uid = self.user.get("id", 0) or 0
                res = self.api.get_user_logs(uid, limit=self.MAX_LOGS)
                if isinstance(res, dict):
                    logs = res.get("logs", []) or []
                elif isinstance(res, list):
                    logs = res

        except Exception:
            logs = []

        normalized: List[Dict[str, Any]] = []
        for log in (logs or [])[: self.MAX_LOGS]:
            method = str(log.get("method") or log.get("action") or "").upper()
            target = (log.get("target") or log.get("target_entity") or log.get("entity") or "")
            details = log.get("details") or log.get("notes") or log.get("message") or ""
            user_name = log.get("user_name") or log.get("username") or log.get("user") or "System"
            ts = str(log.get("timestamp") or log.get("log_time") or "")

            if method and target:
                action_txt = f"{method} {target}"
            else:
                action_txt = str(log.get("action") or log.get("message") or "Activity")

            if details:
                d = str(details).strip()
                if len(d) > 80:
                    d = d[:77] + "..."
                action_txt = f"{action_txt} — {d}"

            normalized.append({"user": user_name, "action": action_txt, "timestamp": ts})

        return normalized

    def _render_page(self):
        logs = self._all_logs or []
        start = (self.current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_logs = logs[start:end]

        self.table.setRowCount(self.PAGE_SIZE)

        for i in range(self.PAGE_SIZE):
            if i < len(page_logs):
                row = page_logs[i]
                self.table.setItem(i, 0, QTableWidgetItem(str(row.get("user", ""))))
                self.table.setItem(i, 1, QTableWidgetItem(str(row.get("action", ""))))
                self.table.setItem(i, 2, QTableWidgetItem(str(row.get("timestamp", ""))))
                for c in range(3):
                    it = self.table.item(i, c)
                    if it:
                        it.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            else:
                for c in range(3):
                    blank = QTableWidgetItem("")
                    blank.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.table.setItem(i, c, blank)

        self.page_label.setText(f"Page {self.current_page} / 2")
        self.btn_prev.setDisabled(self.current_page <= 1)
        has_page2 = len(self._all_logs) > self.PAGE_SIZE
        self.btn_next.setDisabled(self.current_page >= 2 or not has_page2)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_page()

    def _next_page(self):
        if self.current_page < 2 and len(self._all_logs) > self.PAGE_SIZE:
            self.current_page += 1
            self._render_page()


# ====================================
# Manager Charts
# ====================================
def _safe_float(x) -> float:
    try:
        return float(x or 0)
    except Exception:
        return 0.0


def _parse_any_date(s: Any) -> Optional[date]:
    if not s:
        return None
    try:
        if isinstance(s, date) and not isinstance(s, datetime):
            return s
        if isinstance(s, datetime):
            return s.date()
        txt = str(s).strip()
        if "T" in txt:
            txt = txt.split("T", 1)[0]
        return datetime.fromisoformat(txt).date()
    except Exception:
        return None


class MatplotlibCard(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("Card")
        self.setStyleSheet("""
            QFrame#Card {
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #DDE3EA;
            }
        """)
        apply_card_shadow(self)

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(14, 12, 14, 12)
        self._root.setSpacing(10)

        header = QLabel(title)
        header.setObjectName("CardTitle")
        self._root.addWidget(header)

    def body_layout(self) -> QVBoxLayout:
        return self._root


class SalesPerformanceChart(MatplotlibCard):
    def __init__(self, api):
        super().__init__("Sales Performance")
        self.api = api
        self.days = 7

        self._top_row = QHBoxLayout()
        self._top_row.setSpacing(8)

        self.btn_1 = QPushButton("1 Day")
        self.btn_7 = QPushButton("7 Days")
        self.btn_30 = QPushButton("30 Days")
        for b in (self.btn_1, self.btn_7, self.btn_30):
            b.setFixedHeight(30)

        self.btn_1.clicked.connect(lambda: self.set_range(1))
        self.btn_7.clicked.connect(lambda: self.set_range(7))
        self.btn_30.clicked.connect(lambda: self.set_range(30))

        self._top_row.addWidget(self.btn_1)
        self._top_row.addWidget(self.btn_7)
        self._top_row.addWidget(self.btn_30)
        self._top_row.addStretch()

        self.body_layout().addLayout(self._top_row)

        if MATPLOTLIB_OK:
            self.fig = Figure(figsize=(5, 3), dpi=100)
            self.canvas = FigureCanvas(self.fig)
            self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.body_layout().addWidget(self.canvas, 1)
        else:
            warn = QLabel("matplotlib is not installed. Chart disabled.")
            warn.setStyleSheet("color: rgba(0,0,0,0.55);")
            self.body_layout().addWidget(warn, 1)

    def set_range(self, days: int):
        self.days = int(days)
        self.refresh()

    def refresh(self):
        if not MATPLOTLIB_OK:
            return

        try:
            end_d = date.today()
            start_d = end_d - timedelta(days=max(0, self.days - 1))
            start_iso = start_d.isoformat()
            end_iso = end_d.isoformat()

            sales_res = self.api.get_sales(start_date=start_iso, end_date=end_iso)
            sales_list = []
            if isinstance(sales_res, dict):
                sales_list = sales_res.get("sales", []) or []
            elif isinstance(sales_res, list):
                sales_list = sales_res

            day_map: Dict[date, Dict[str, float]] = {}
            cursor = start_d
            while cursor <= end_d:
                day_map[cursor] = {"amount": 0.0, "qty": 0.0}
                cursor += timedelta(days=1)

            for s in sales_list:
                d = (
                    _parse_any_date(s.get("sale_date"))
                    or _parse_any_date(s.get("date"))
                    or _parse_any_date(s.get("timestamp"))
                    or _parse_any_date(s.get("created_at"))
                )
                if not d or d not in day_map:
                    continue

                day_map[d]["amount"] += _safe_float(s.get("total_amount"))

                items = s.get("items") or s.get("sale_items") or []
                if isinstance(items, list):
                    for it in items:
                        day_map[d]["qty"] += _safe_float(it.get("quantity") or it.get("quantity_sold") or 0)

            xs = sorted(day_map.keys())
            xlabels = [d.strftime("%b %d") for d in xs]
            revenue = [day_map[d]["amount"] for d in xs]
            qty = [day_map[d]["qty"] for d in xs]

            self.fig.clear()
            ax = self.fig.add_subplot(111)

            ax.plot(xlabels, revenue, marker="o", linewidth=2, label="Total Amount")
            if any(v > 0 for v in qty):
                ax.plot(xlabels, qty, marker="o", linewidth=2, label="Total Quantity Sold")

            ax.set_title(f"Last {self.days} day(s)")
            ax.tick_params(axis="x", rotation=35)
            ax.grid(True, alpha=0.25)
            ax.legend(loc="upper left")

            self.fig.tight_layout()
            self.canvas.draw()

        except Exception:
            traceback.print_exc()
            try:
                self.fig.clear()
                ax = self.fig.add_subplot(111)
                ax.text(0.5, 0.5, "Failed to load sales chart data.", ha="center", va="center")
                ax.axis("off")
                self.canvas.draw()
            except Exception:
                pass


class CategoryPieChart(MatplotlibCard):
    @dataclass
    class Slice:
        name: str
        value: float
        color: str

    def __init__(self, api):
        super().__init__("Category Distribution")
        self.api = api

        self.legend_wrap = QFrame()
        self.legend_wrap.setStyleSheet("background: transparent;")
        self.legend_grid = QGridLayout(self.legend_wrap)
        self.legend_grid.setContentsMargins(0, 0, 0, 0)
        self.legend_grid.setHorizontalSpacing(12)
        self.legend_grid.setVerticalSpacing(8)

        if MATPLOTLIB_OK:
            self.fig = Figure(figsize=(4, 3), dpi=100)
            self.canvas = FigureCanvas(self.fig)
            self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.body_layout().addWidget(self.canvas, 1)
        else:
            warn = QLabel("matplotlib is not installed. Chart disabled.")
            warn.setStyleSheet("color: rgba(0,0,0,0.55);")
            self.body_layout().addWidget(warn, 1)

        self.body_layout().addWidget(self.legend_wrap)

        self.palette = [
            "#2563EB", "#DC2626", "#16A34A", "#F59E0B", "#7C3AED",
            "#0EA5E9", "#DB2777", "#84CC16", "#FB7185"
        ]
        self.others_color = "#9CA3AF"

    def _clear_legend(self):
        while self.legend_grid.count():
            item = self.legend_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _legend_item(self, color: str, text: str) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        swatch = QLabel()
        swatch.setFixedSize(12, 12)
        swatch.setStyleSheet(f"background: {color}; border-radius: 3px;")

        lbl = QLabel(text)
        lbl.setStyleSheet("color: rgba(0,0,0,0.72); font-size: 12px;")

        row.addWidget(swatch)
        row.addWidget(lbl)
        row.addStretch()
        return w

    def refresh(self):
        self._clear_legend()

        if not MATPLOTLIB_OK:
            return

        try:
            res = self.api.get_category_distribution_report()
            categories = []
            if isinstance(res, dict):
                categories = res.get("categories", []) or []
            elif isinstance(res, list):
                categories = res

            def score(c):
                return (_safe_float(c.get("total_stock_quantity")), _safe_float(c.get("percentage_share")))

            categories_sorted = sorted(categories, key=score, reverse=True)

            top9 = categories_sorted[:9]
            rest = categories_sorted[9:]

            slices: List[CategoryPieChart.Slice] = []
            for idx, c in enumerate(top9):
                name = str(c.get("category_name") or c.get("name") or f"Category {idx+1}")
                val = _safe_float(c.get("total_stock_quantity") or c.get("percentage_share") or 0)
                slices.append(self.Slice(name=name, value=val, color=self.palette[idx % len(self.palette)]))

            others_val = 0.0
            for c in rest:
                others_val += _safe_float(c.get("total_stock_quantity") or c.get("percentage_share") or 0)

            if others_val > 0:
                slices.append(self.Slice(name="Others", value=others_val, color=self.others_color))
            elif len(slices) < 10:
                slices.append(self.Slice(name="Others", value=0.0, color=self.others_color))

            slices = slices[:10]

            values = [max(0.0, s.value) for s in slices]
            colors = [s.color for s in slices]

            self.fig.clear()
            ax = self.fig.add_subplot(111)

            if sum(values) <= 0:
                ax.text(0.5, 0.5, "No category data yet.", ha="center", va="center")
                ax.axis("off")
            else:
                ax.pie(values, labels=None, colors=colors, startangle=90)
                ax.set_title("Top Categories (Top 9 + Others)")

            self.fig.tight_layout()
            self.canvas.draw()

            for i, s in enumerate(slices):
                r = i // 5
                c = i % 5
                self.legend_grid.addWidget(self._legend_item(s.color, s.name), r, c)

        except Exception:
            traceback.print_exc()
            try:
                self.fig.clear()
                ax = self.fig.add_subplot(111)
                ax.text(0.5, 0.5, "Failed to load category chart data.", ha="center", va="center")
                ax.axis("off")
                self.canvas.draw()
            except Exception:
                pass


# ====================================
# Retailer: Progress Tracker + Leaderboard
# ====================================
def _peso_p(value: Any) -> str:
    try:
        return f"P{float(value):,.2f}"
    except Exception:
        return "P0.00"


class RetailerProgressTrackerCard(QFrame):
    """
    Left panel:
    - Title "Progress Tracker"
    - Motivational quota message
    - Thin rounded progress bar for goal
    - Current Status card:
        - Streak row (🔥 + number)
        - Toggle buttons (Today / Overall)
        - Sales amount label that changes based on toggle
    """
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")
        self.setStyleSheet("""
            QFrame#Card {
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #DDE3EA;
            }
        """)
        apply_card_shadow(self)

        self._mode = "today"
        self._sales_today = 0.0
        self._sales_overall = 0.0
        self._streak = 0
        self._goal = 1000.0

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        self.lbl_title = QLabel("Progress Tracker")
        self.lbl_title.setObjectName("CardTitle")
        root.addWidget(self.lbl_title)

        self.lbl_msg = QLabel("Complete the P1,000.00 amount of sale to reach your daily quota.")
        self.lbl_msg.setWordWrap(True)
        self.lbl_msg.setStyleSheet("color: rgba(0,0,0,0.60);")
        root.addWidget(self.lbl_msg)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E5E7EB;
                border-radius: 5px;
                background: #F3F4F6;
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background: #1E3A8A;
            }
        """)
        root.addWidget(self.progress)

        self.status_card = QFrame()
        self.status_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 14px;
                border: 1px solid #EEF2F7;
            }
        """)
        status_l = QVBoxLayout(self.status_card)
        status_l.setContentsMargins(14, 12, 14, 12)
        status_l.setSpacing(10)

        # Streak row
        streak_row = QHBoxLayout()
        streak_row.setSpacing(8)

        self.lbl_fire = QLabel("🔥")
        self.lbl_fire.setStyleSheet("font-size: 16px;")
        streak_row.addWidget(self.lbl_fire)

        self.lbl_streak = QLabel("Streak: 0")
        self.lbl_streak.setStyleSheet("font-weight: 600; color: rgba(0,0,0,0.78);")
        streak_row.addWidget(self.lbl_streak)
        streak_row.addStretch()
        status_l.addLayout(streak_row)

        # Toggle row + amount
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(10)

        self.btn_today = QPushButton("Today")
        self.btn_overall = QPushButton("Overall")

        for b in (self.btn_today, self.btn_overall):
            b.setFixedHeight(32)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet("""
                QPushButton {
                    border: 1px solid #DDE3EA;
                    border-radius: 10px;
                    padding: 6px 10px;
                    background: #FFFFFF;
                }
                QPushButton:hover {
                    background: #F3F4F6;
                }
            """)

        self.btn_today.clicked.connect(lambda: self.set_mode("today"))
        self.btn_overall.clicked.connect(lambda: self.set_mode("overall"))

        toggle_row.addWidget(self.btn_today)
        toggle_row.addWidget(self.btn_overall)
        toggle_row.addStretch()

        self.lbl_amount = QLabel("P0.00")
        self.lbl_amount.setStyleSheet("font-size: 18px; font-weight: 800; color: #1E3A8A;")
        toggle_row.addWidget(self.lbl_amount)

        status_l.addLayout(toggle_row)
        root.addWidget(self.status_card)

        root.addStretch()
        self._apply_mode_styles()
        self._update_amount_label()

    def set_mode(self, mode: str):
        mode = (mode or "").lower().strip()
        if mode not in ("today", "overall"):
            mode = "today"
        self._mode = mode
        self._apply_mode_styles()
        self._update_amount_label()

    def _apply_mode_styles(self):
        active = """
            QPushButton {
                border: 1px solid #1E3A8A;
                border-radius: 10px;
                padding: 6px 10px;
                background: #1E3A8A;
                color: #FFFFFF;
                font-weight: 700;
            }
        """
        inactive = """
            QPushButton {
                border: 1px solid #DDE3EA;
                border-radius: 10px;
                padding: 6px 10px;
                background: #FFFFFF;
                color: rgba(0,0,0,0.78);
                font-weight: 600;
            }
            QPushButton:hover {
                background: #F3F4F6;
            }
        """
        if self._mode == "today":
            self.btn_today.setStyleSheet(active)
            self.btn_overall.setStyleSheet(inactive)
        else:
            self.btn_overall.setStyleSheet(active)
            self.btn_today.setStyleSheet(inactive)

    def _update_amount_label(self):
        if self._mode == "today":
            self.lbl_amount.setText(_peso_p(self._sales_today))
        else:
            self.lbl_amount.setText(_peso_p(self._sales_overall))

    def update_data(self, *, sales_today: float, sales_overall: float, streak: int, quota_goal: float):
        self._sales_today = float(sales_today or 0)
        self._sales_overall = float(sales_overall or 0)
        self._streak = int(streak or 0)
        self._goal = float(quota_goal or 0) if float(quota_goal or 0) > 0 else 1000.0

        self.lbl_streak.setText(f"Streak: {self._streak}")

        # Message uses quota goal
        self.lbl_msg.setText(f"Complete the {_peso_p(self._goal)} amount of sale to reach your daily quota.")

        # Progress based on today's sales vs goal
        pct = 0
        try:
            pct = int(round((self._sales_today / self._goal) * 100)) if self._goal > 0 else 0
        except Exception:
            pct = 0
        pct = max(0, min(100, pct))
        self.progress.setValue(pct)

        self._update_amount_label()


class RetailerLeaderboardCard(QFrame):
    """
    Right panel:
    - Title "Leaderboard"
    - Table Top 10 Retailers
      Columns: Streak (3-digit), Full Name, Sales Amount (PXXX.XX)
    """
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")
        self.setStyleSheet("""
            QFrame#Card {
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #DDE3EA;
            }
        """)
        apply_card_shadow(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        title = QLabel("Leaderboard")
        title.setObjectName("CardTitle")
        root.addWidget(title)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Streak", "Full Name", "Sales Amount"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(320)

        try:
            hh = self.table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        except Exception:
            pass

        try:
            vh = self.table.verticalHeader()
            vh.setVisible(False)
            vh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        except Exception:
            pass

        root.addWidget(self.table, 1)

    def render(self, rows: List[Dict[str, Any]]):
        self.table.setRowCount(0)
        for r in (rows or [])[:10]:
            row = self.table.rowCount()
            self.table.insertRow(row)

            streak = int(_safe_float(r.get("current_streak") or r.get("streak") or 0))
            full_name = str(r.get("full_name") or r.get("name") or r.get("retailer_name") or "—")

            sales_amount = (
                r.get("total_sales")
                or r.get("sales_amount")
                or r.get("total_amount")
                or r.get("sales")
                or 0
            )
            sales_amount_f = float(_safe_float(sales_amount))

            self.table.setItem(row, 0, QTableWidgetItem("{:03d}".format(streak)))
            self.table.setItem(row, 1, QTableWidgetItem(full_name))
            self.table.setItem(row, 2, QTableWidgetItem(_peso_p(sales_amount_f)))

        # keep UI tidy if empty
        if self.table.rowCount() == 0:
            self.table.setRowCount(1)
            for c in range(3):
                blank = QTableWidgetItem("No data")
                blank.setFlags(Qt.ItemFlag.NoItemFlags)
                self.table.setItem(0, c, blank)


# ====================================
# MAIN DASHBOARD PAGE (Role-aware)
# ====================================
class DashboardPage(QWidget):
    """
    Emits view_activity_requested when the user clicks 'View More'
    in the Recent Activity panel (admin only).
    """
    view_activity_requested = pyqtSignal()

    def __init__(self, user_data=None):
        super().__init__()
        self.user = user_data or {}
        self.role = (self.user.get("role") or "").lower()
        self.api = get_api()

        self._build_ui()
        self.refresh_dashboard_data()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_dashboard_data)
        self.timer.start(20000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(24)
        root.setContentsMargins(32, 32, 32, 32)

        user_name = self.user.get("full_name", "User")
        title = QLabel(f"Dashboard – Welcome, {user_name}")
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: 700;
            color: #0A0A0A;
            background: transparent;
        """)
        root.addWidget(title)

        # KPI GRID (role-aware labels)
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setHorizontalSpacing(22)
        self.kpi_grid.setVerticalSpacing(18)

        self.card_1 = DashboardCard("—")
        self.card_2 = DashboardCard("—")
        self.card_3 = DashboardCard("—")
        self.card_4 = DashboardCard("—")

        self.kpi_grid.addWidget(self.card_1, 0, 0)
        self.kpi_grid.addWidget(self.card_2, 0, 1)
        self.kpi_grid.addWidget(self.card_3, 0, 2)
        self.kpi_grid.addWidget(self.card_4, 0, 3)

        root.addLayout(self.kpi_grid)

        # Body (role-based)
        if self.role == "admin":
            self.activity_preview = RecentActivityPreview(self.user, self.api)
            self.activity_preview.view_more_clicked.connect(self.view_activity_requested.emit)
            root.addWidget(self.activity_preview, 1)

            self.manager_sales_chart = None
            self.manager_category_chart = None

            self.retailer_progress = None
            self.retailer_leaderboard = None

        elif self.role == "manager":
            charts_row = QHBoxLayout()
            charts_row.setSpacing(16)

            self.manager_sales_chart = SalesPerformanceChart(self.api)
            self.manager_category_chart = CategoryPieChart(self.api)

            charts_row.addWidget(self.manager_sales_chart, 2)
            charts_row.addWidget(self.manager_category_chart, 2)

            root.addLayout(charts_row)

            self.activity_preview = None

            self.retailer_progress = None
            self.retailer_leaderboard = None

        else:
            # Retailer split layout: left progress tracker, right leaderboard (2/3 width)
            self.activity_preview = None
            self.manager_sales_chart = None
            self.manager_category_chart = None

            split = QHBoxLayout()
            split.setSpacing(16)

            self.retailer_progress = RetailerProgressTrackerCard()
            self.retailer_leaderboard = RetailerLeaderboardCard()

            split.addWidget(self.retailer_progress, 1)
            split.addWidget(self.retailer_leaderboard, 2)

            root.addLayout(split, 1)

    # ========================================================================
    # DATA REFRESH
    # ========================================================================
    def refresh_dashboard_data(self):
        try:
            if self.role == "admin":
                self._refresh_admin()
            elif self.role == "manager":
                self._refresh_manager()
            else:
                self._refresh_retailer()
        except Exception:
            print("\n>>> DASHBOARD FETCH ERROR <<<")
            traceback.print_exc()

    # ------------------------
    # Admin Dashboard
    # ------------------------
    def _refresh_admin(self):
        """
        ✅ FIXED: use backend route GET /api/v1/dashboard/admin
        so Total Revenue + Total Sales Count always display correctly.
        """
        self.card_1.title_lbl.setText("Total Revenue")
        self.card_2.title_lbl.setText("Total Sales Count")
        self.card_3.title_lbl.setText("Total Products")
        self.card_4.title_lbl.setText("Total Users")

        try:
            res = self.api.get_admin_dashboard()  # GET /dashboard/admin

            total_users = int(_safe_float(res.get("total_users")))
            total_products = int(_safe_float(res.get("total_products")))
            total_sales_count = int(_safe_float(res.get("total_sales_count")))
            total_revenue = float(_safe_float(res.get("total_revenue")))

            self.card_4.set_value(str(total_users))
            self.card_3.set_value(str(total_products))
            self.card_2.set_value(str(total_sales_count))
            self.card_1.set_value(f"₱{total_revenue:,.2f}")

        except Exception:
            traceback.print_exc()
            self.card_1.set_value("₱0.00")
            self.card_2.set_value("0")
            self.card_3.set_value("0")
            self.card_4.set_value("0")

        if self.activity_preview:
            self.activity_preview.refresh()

    # ------------------------
    # Manager Dashboard
    # ------------------------
    def _refresh_manager(self):
        self.card_1.title_lbl.setText("Low Stock Count")
        self.card_2.title_lbl.setText("Expiring (7d)")
        self.card_3.title_lbl.setText("Revenue (30d)")
        self.card_4.title_lbl.setText("Qty Sold (30d)")

        products_data = self.api.get_products(per_page=9999)
        prods = products_data.get("products", []) or []
        low_stock = [
            p for p in prods
            if _safe_float(p.get("stock_level")) <= _safe_float(p.get("min_stock_level", 1))
        ]
        self.card_1.set_value(str(len(low_stock)))

        expiring_count = 0
        try:
            ar = self.api.get_alerts_report(days_ahead=7)
            summary = ar.get("summary", {}) or {}
            expiring_count = int(summary.get("total_alerts", 0) or 0)
        except Exception:
            expiring_count = 0
        self.card_2.set_value(str(expiring_count))

        qty_sold_30d = 0.0
        rev_30d = 0.0
        try:
            end_d = date.today()
            start_d = end_d - timedelta(days=29)
            sales_data = self.api.get_sales(start_date=start_d.isoformat(), end_date=end_d.isoformat())
            sales_list = sales_data.get("sales", []) or []
            for s in sales_list:
                rev_30d += _safe_float(s.get("total_amount"))
                items = s.get("items") or s.get("sale_items") or []
                if isinstance(items, list):
                    for it in items:
                        qty_sold_30d += _safe_float(it.get("quantity") or it.get("quantity_sold") or 0)
        except Exception:
            pass

        self.card_3.set_value(f"₱{int(rev_30d):,}")
        self.card_4.set_value(str(int(qty_sold_30d)))

        if self.manager_sales_chart:
            self.manager_sales_chart.refresh()
        if self.manager_category_chart:
            self.manager_category_chart.refresh()

    # ------------------------
    # Retailer Dashboard
    # ------------------------
    def _refresh_retailer(self):
        self.card_1.title_lbl.setText("Sales Today")
        self.card_2.title_lbl.setText("Total Sales")
        self.card_3.title_lbl.setText("Transactions")
        self.card_4.title_lbl.setText("Quota %")

        uid = self.user.get("id")
        if not uid:
            self.card_1.set_value("₱0")
            self.card_2.set_value("₱0")
            self.card_3.set_value("0")
            self.card_4.set_value("0%")
            return

        # Retailer metrics for left panel + KPI cards
        sales_today = 0.0
        total_sales = 0.0
        tx = 0
        quota = 1000.0
        quota_progress = 0.0
        streak = 0

        try:
            metrics = self.api.get_retailer_metrics(int(uid))

            # support both shapes (flat keys or nested personal_sales_stats)
            sales_today = _safe_float(metrics.get("sales_today") or metrics.get("personal_sales_stats", {}).get("sales_today"))
            total_sales = _safe_float(metrics.get("total_sales") or metrics.get("personal_sales_stats", {}).get("total_sales"))
            tx = int(_safe_float(metrics.get("total_transactions") or metrics.get("personal_sales_stats", {}).get("total_transactions")))
            quota = _safe_float(metrics.get("daily_quota") or 1000.0) or 1000.0
            quota_progress = _safe_float(metrics.get("quota_progress") or 0.0)
            streak = int(_safe_float(metrics.get("current_streak") or 0))

        except Exception:
            traceback.print_exc()

        self.card_1.set_value(f"₱{int(sales_today):,}")
        self.card_2.set_value(f"₱{int(total_sales):,}")
        self.card_3.set_value(str(tx))
        self.card_4.set_value(f"{int(quota_progress)}%")

        # Left progress tracker card
        if self.retailer_progress:
            self.retailer_progress.update_data(
                sales_today=sales_today,
                sales_overall=total_sales,
                streak=streak,
                quota_goal=quota,
            )

        # Right leaderboard
        if self.retailer_leaderboard:
            rows: List[Dict[str, Any]] = []
            try:
                lb = self.api.get_leaderboard(limit=10)
                if isinstance(lb, dict):
                    rows = (
                        lb.get("leaderboard")
                        or lb.get("retailers")
                        or lb.get("data")
                        or lb.get("results")
                        or []
                    )
                elif isinstance(lb, list):
                    rows = lb
            except Exception:
                rows = []

            self.retailer_leaderboard.render(rows)
