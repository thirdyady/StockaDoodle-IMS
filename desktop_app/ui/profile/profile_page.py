# desktop_app/ui/profile/profile_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QTextEdit, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt

class ProfilePage(QWidget):
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(24)


        header = QHBoxLayout()
        name = self.user_data.get("full_name", self.user_data.get("username", "User"))
        htitle = QLabel(f"Profile — {name}")
        htitle.setObjectName("title")
        header.addWidget(htitle)
        header.addStretch()
        root.addLayout(header)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        info = QWidget()
        info_l = QVBoxLayout(info)
        info_l.setContentsMargins(12,12,12,12)
        info_card = QFrame()
        info_card.setObjectName("Card")
        ic_layout = QVBoxLayout(info_card)
        ic_layout.setContentsMargins(12,12,12,12)
        ic_layout.addWidget(QLabel("Full name"))
        self.full_name = QLineEdit(self.user_data.get("full_name", ""))
        ic_layout.addWidget(self.full_name)
        ic_layout.addWidget(QLabel("Email"))
        self.email = QLineEdit(self.user_data.get("email", ""))
        ic_layout.addWidget(self.email)
        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("primaryBtn")
        ic_layout.addWidget(save_btn)
        info_l.addWidget(info_card)
        tabs.addTab(info, "Information")

        security = QWidget()
        sec_l = QVBoxLayout(security)
        sec_card = QFrame()
        sec_card.setObjectName("Card")
        sc_layout = QVBoxLayout(sec_card)
        sc_layout.addWidget(QLabel("Change password"))
        curr = QLineEdit(); curr.setPlaceholderText("Current password"); curr.setEchoMode(QLineEdit.EchoMode.Password)
        sc_layout.addWidget(curr)
        newp = QLineEdit(); newp.setPlaceholderText("New password"); newp.setEchoMode(QLineEdit.EchoMode.Password)
        sc_layout.addWidget(newp)
        pwd_btn = QPushButton("Change Password"); pwd_btn.setObjectName("secondaryBtn"); sc_layout.addWidget(pwd_btn)
        sc_layout.addSpacing(8)
        sc_layout.addWidget(QLabel("Two-Factor Authentication"))
        sc_layout.addWidget(QLabel("MFA can be enabled for Admin/Manager accounts via backend."))
        sec_l.addWidget(sec_card)
        tabs.addTab(security, "Security")

        activity = QWidget()
        a_l = QVBoxLayout(activity)
        act_card = QFrame()
        act_card.setObjectName("Card")
        act_layout = QVBoxLayout(act_card)
        act_layout.setContentsMargins(12,12,12,12)
        act_layout.addWidget(QLabel("Recent logins and activity"))
        activity_text = QTextEdit()
        activity_text.setReadOnly(True)
        activity_text.setPlainText("Recent actions will appear here.")
        act_layout.addWidget(activity_text)
        a_l.addWidget(act_card)
        tabs.addTab(activity, "Activity")

        root.addWidget(tabs)
