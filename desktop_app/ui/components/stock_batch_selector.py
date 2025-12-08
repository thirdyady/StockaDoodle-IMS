# desktop_app/ui/components/stock_batch_selector.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush
from typing import Dict, List, Optional
from datetime import datetime, date

from desktop_app.utils.helpers import format_date, get_feather_icon
from desktop_app.utils.api_wrapper import (
    delete_stock_batch, get_current_user_data
)
from desktop_app.ui.components.add_batch_dialog import AddBatchDialog
from desktop_app.ui.components.edit_batch_dialog import EditBatchDialog
from desktop_app.ui.components.batch_dispose_dialog import BatchDisposeDialog


class StockBatchSelector(QWidget):
    """
    Stock batch selector widget with table view and action buttons.
    Displays batches with color-coded expiry dates and quantities.
    """

    batches_updated = pyqtSignal()

    def __init__(self, product_id: int, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.batches: List[Dict] = []
        self.selected_batch: Optional[Dict] = None

        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # -------------------------------------------------
        # Header row
        # -------------------------------------------------
        header_row = QHBoxLayout()
        title = QLabel("Stock Batches")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0A2A83;")
        header_row.addWidget(title)
        header_row.addStretch()

        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(get_feather_icon("refresh-cw", 16))
        self.refresh_btn.setToolTip("Refresh batches")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #D9E4FF;
                background: #F3F6FF;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #E8EEFF;
            }
        """)
        self.refresh_btn.clicked.connect(self.batches_updated.emit)
        header_row.addWidget(self.refresh_btn)

        layout.addLayout(header_row)

        # -------------------------------------------------
        # Table
        # -------------------------------------------------
        self.batch_table = QTableWidget()
        self.batch_table.setColumnCount(5)
        self.batch_table.setHorizontalHeaderLabels([
            "Batch #", "Quantity", "Expiry Date", "Status", "Reason"
        ])
        self.batch_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.batch_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.batch_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.batch_table.setAlternatingRowColors(True)
        self.batch_table.verticalHeader().setVisible(False)

        # Instead of hard max height, let the parent decide
        self.batch_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.batch_table.setMinimumHeight(220)

        self.batch_table.itemSelectionChanged.connect(self._on_selection_changed)

        header = self.batch_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.batch_table, 1)

        # -------------------------------------------------
        # Action buttons container
        # -------------------------------------------------
        btn_card = QFrame()
        btn_card.setObjectName("btnCard")

        btn_layout = QHBoxLayout(btn_card)
        btn_layout.setContentsMargins(10, 10, 10, 10)
        btn_layout.setSpacing(8)

        self.btn_add = QPushButton("➕ Add New Batch")
        self.btn_add.setObjectName("primaryBtn")
        self.btn_add.setFixedHeight(36)
        self.btn_add.clicked.connect(self._on_add_batch)

        self.btn_edit = QPushButton("✏️ Edit Batch")
        self.btn_edit.setObjectName("secondaryBtn")
        self.btn_edit.setFixedHeight(36)
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._on_edit_batch)

        self.btn_dispose = QPushButton("🗑️ Dispose")
        self.btn_dispose.setObjectName("warningBtn")
        self.btn_dispose.setFixedHeight(36)
        self.btn_dispose.setEnabled(False)
        self.btn_dispose.clicked.connect(self._on_dispose_batch)

        self.btn_delete = QPushButton("❌ Delete")
        self.btn_delete.setObjectName("dangerBtn")
        self.btn_delete.setFixedHeight(36)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete_batch)

        # Let buttons expand evenly to avoid clipping
        for b in (self.btn_add, self.btn_edit, self.btn_dispose, self.btn_delete):
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_dispose)
        btn_layout.addWidget(self.btn_delete)

        layout.addWidget(btn_card)

    def _apply_styles(self):
        self.batch_table.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF;
                border: 1px solid #DDE3EA;
                border-radius: 8px;
                gridline-color: #E3E8F5;
            }
            QHeaderView::section {
                background-color: #F4F6FD;
                padding: 10px;
                border: none;
                font-weight: 600;
                font-size: 12px;
                color: #0A2A83;
            }
            QTableWidget::item {
                padding: 8px 4px;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background: #E6ECFF;
                color: #0A2A83;
            }
        """)

        self.setStyleSheet("""
            #btnCard {
                background: #FFFFFF;
                border: 1px solid #E5EAF5;
                border-radius: 10px;
            }

            QPushButton {
                padding: 8px 12px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton#primaryBtn {
                background: #0A2A83;
                color: white;
            }
            QPushButton#primaryBtn:hover {
                background: #153AAB;
            }
            QPushButton#secondaryBtn {
                background: #F3F6FF;
                color: #0A2A83;
                border: 1px solid #D9E4FF;
            }
            QPushButton#secondaryBtn:hover {
                background: #E8EEFF;
            }
            QPushButton#secondaryBtn:disabled {
                background: #F8FAFC;
                color: #CBD5E1;
                border: 1px solid #E2E6EE;
            }
            QPushButton#warningBtn {
                background: #F59E0B;
                color: white;
            }
            QPushButton#warningBtn:hover {
                background: #D97706;
            }
            QPushButton#warningBtn:disabled {
                background: #F8FAFC;
                color: #CBD5E1;
            }
            QPushButton#dangerBtn {
                background: #EF4444;
                color: white;
            }
            QPushButton#dangerBtn:hover {
                background: #DC2626;
            }
            QPushButton#dangerBtn:disabled {
                background: #F8FAFC;
                color: #CBD5E1;
            }
        """)

    def _get_expiry_status(self, expiry_date_str: Optional[str]) -> tuple:
        if not expiry_date_str:
            return "#94A3B8", "No expiry", "#F8FAFC"

        try:
            expiry_date = datetime.fromisoformat(expiry_date_str.replace("Z", "")).date()
            today = date.today()
            days_until = (expiry_date - today).days

            if days_until < 0:
                return "#EF4444", "Expired", "#FEF2F2"
            elif days_until <= 30:
                return "#F59E0B", f"{days_until}d left", "#FFFBEB"
            else:
                return "#10B981", "Good", "#F0FDF4"
        except Exception:
            return "#94A3B8", "Unknown", "#F8FAFC"

    def load_batches(self, batches: List[Dict]):
        self.batches = batches
        self.batch_table.setRowCount(0)
        self.selected_batch = None
        self._update_button_states()

        if not batches:
            self.batch_table.setRowCount(1)
            item = QTableWidgetItem("No stock batches available")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor("#94A3B8"))
            self.batch_table.setItem(0, 0, item)
            self.batch_table.setSpan(0, 0, 1, 5)
            return

        sorted_batches = sorted(
            batches,
            key=lambda b: (
                b.get("expiration_date") or "9999-12-31",
                b.get("id", 0)
            )
        )

        self.batch_table.setRowCount(len(sorted_batches))

        for row, batch in enumerate(sorted_batches):
            batch_id = batch.get("id", "?")
            quantity = batch.get("quantity", 0)
            expiry_str = batch.get("expiration_date")
            reason = batch.get("reason", "")

            batch_item = QTableWidgetItem(f"#{batch_id}")
            batch_item.setData(Qt.ItemDataRole.UserRole, batch)
            batch_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.batch_table.setItem(row, 0, batch_item)

            qty_item = QTableWidgetItem(f"{quantity:,} units")
            qty_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            qty_item.setData(Qt.ItemDataRole.UserRole, batch)
            if quantity == 0:
                qty_item.setForeground(QColor("#94A3B8"))
            self.batch_table.setItem(row, 1, qty_item)

            if expiry_str:
                try:
                    expiry_formatted = format_date(expiry_str, "%b %d, %Y")
                except Exception:
                    expiry_formatted = str(expiry_str)
            else:
                expiry_formatted = "No expiry"

            expiry_item = QTableWidgetItem(expiry_formatted)
            expiry_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            expiry_item.setData(Qt.ItemDataRole.UserRole, batch)
            self.batch_table.setItem(row, 2, expiry_item)

            status_color, status_text, bg_color = self._get_expiry_status(expiry_str)
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            status_item.setData(Qt.ItemDataRole.UserRole, batch)
            status_item.setForeground(QColor(status_color))
            status_item.setBackground(QBrush(QColor(bg_color)))
            self.batch_table.setItem(row, 3, status_item)

            reason_item = QTableWidgetItem(reason or "—")
            reason_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            reason_item.setData(Qt.ItemDataRole.UserRole, batch)
            reason_item.setForeground(QColor("#64748b"))
            self.batch_table.setItem(row, 4, reason_item)

    def _on_selection_changed(self):
        selected_items = self.batch_table.selectedItems()
        if selected_items:
            first_item = selected_items[0]
            batch = first_item.data(Qt.ItemDataRole.UserRole)
            self.selected_batch = batch if batch else None
        else:
            self.selected_batch = None

        self._update_button_states()

    def _update_button_states(self):
        has_selection = self.selected_batch is not None
        self.btn_edit.setEnabled(has_selection)

        if has_selection:
            qty = self.selected_batch.get("quantity", 0)
            self.btn_dispose.setEnabled(qty > 0)
            self.btn_delete.setEnabled(qty == 0)
        else:
            self.btn_dispose.setEnabled(False)
            self.btn_delete.setEnabled(False)

    def _on_add_batch(self):
        dialog = AddBatchDialog(self.product_id, parent=self)
        if dialog.exec():
            self.batches_updated.emit()

    def _on_edit_batch(self):
        if not self.selected_batch:
            return

        dialog = EditBatchDialog(self.product_id, self.selected_batch, parent=self)
        if dialog.exec():
            self.batches_updated.emit()

    def _on_dispose_batch(self):
        if not self.selected_batch:
            return

        dialog = BatchDisposeDialog(self.product_id, self.selected_batch, parent=self)
        if dialog.exec():
            self.batches_updated.emit()

    def _on_delete_batch(self):
        if not self.selected_batch:
            return

        batch_id = self.selected_batch.get("id")
        qty = self.selected_batch.get("quantity", 0)

        if qty > 0:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                f"Batch #{batch_id} still has {qty} units. Please dispose all stock first."
            )
            return

        reply = QMessageBox.question(
            self,
            "Delete Batch",
            f"Are you sure you want to delete empty Batch #{batch_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            user_data = get_current_user_data()
            user_id = user_data.get("id") if user_data else None

            result = delete_stock_batch(self.product_id, batch_id, user_id=user_id)

            if isinstance(result, dict) and result.get("message"):
                QMessageBox.information(self, "Success", "Batch deleted successfully!")
                self.batches_updated.emit()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete batch. Please try again.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete batch:\n{str(e)}")
