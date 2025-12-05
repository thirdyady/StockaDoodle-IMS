# desktop_app/ui/main_window.py
import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from ui.header_bar import HeaderBar
from ui.side_bar import SideBar

from ui.pages.dashboard import DashboardPage
from ui.pages.products.product_list import ProductListPage
from ui.sales.sales_management import SalesManagementPage
from ui.reports.reports_page import ReportsPage
from ui.profile.profile_page import ProfilePage

from utils.theme import load_light_theme


class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()

        self.user_data = user_data or {}

        print(">>> USING MAIN WINDOW FROM:", os.path.abspath(__file__))

        self.setWindowTitle("StockaDoodle – Dashboard")
        self.resize(1400, 900)

        self.setStyleSheet(load_light_theme())

        # App icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "stockadoodle-transparent.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # LEFT SIDE – Sidebar
        self.sidebar = SideBar(self.user_data)
        root_layout.addWidget(self.sidebar)

        # RIGHT SIDE – Content
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # HEADER BAR
        self.header = HeaderBar(self.user_data)
        self.header.toggle_sidebar.connect(self.toggle_sidebar)
        content_layout.addWidget(self.header)

        # STACKED PAGES
        self.pages = QStackedWidget()
        content_layout.addWidget(self.pages)

        self.dashboard_page = DashboardPage(self.user_data)
        self.products_page = ProductListPage()
        self.sales_page = SalesManagementPage()
        self.reports_page = ReportsPage()
        self.profile_page = ProfilePage(self.user_data)

        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.products_page)
        self.pages.addWidget(self.sales_page)
        self.pages.addWidget(self.reports_page)
        self.pages.addWidget(self.profile_page)

        root_layout.addWidget(content_container)

        # Page switch
        self.sidebar.menu.currentRowChanged.connect(self.pages.setCurrentIndex)

    def toggle_sidebar(self):
        """Toggle without animation & without layout breaking."""
        self.sidebar.setVisible(not self.sidebar.isVisible())
