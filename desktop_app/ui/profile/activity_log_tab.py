# desktop_app/ui/profile/activity_log_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton
from PyQt6.QtCore import Qt

class ActivityLogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8,8,8,8)
        title = QLabel("Activity Log")
        title.setObjectName("title")
        root.addWidget(title)

        table = QTableWidget(6, 4)
        table.setHorizontalHeaderLabels(["Date", "User", "Action", "Details"])
        sample = [
            ("2025-12-01 09:12", "admin", "create_user", "Created user: john"),
            ("2025-12-01 10:00", "manager", "update_product", "Updated: Soda 300ml"),
            ("2025-12-02 11:30", "retailer1", "sale", "Sale ID: 124"),
        ]
        for r, row in enumerate(sample):
            for c, v in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(str(v)))
        root.addWidget(table)

        export_btn = QPushButton("Export CSV")
        export_btn.setObjectName("ghost")
        root.addWidget(export_btn)
