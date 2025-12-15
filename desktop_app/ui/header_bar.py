# desktop_app/ui/header_bar.py

from __future__ import annotations

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal


class HeaderBar(QWidget):
    """
    Compatibility stub.

    The UI has moved away from using a top header.
    We keep this class to avoid breaking older imports.
    """

    toggle_sidebar = pyqtSignal()
    view_profile_requested = pyqtSignal()

    def __init__(self, user_data=None):
        super().__init__()
        self.setObjectName("headerBar")

        # Make it effectively invisible in layout if ever used.
        self.setFixedHeight(0)
        self.setMinimumHeight(0)
        self.setMaximumHeight(0)
