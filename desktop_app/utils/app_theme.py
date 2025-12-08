# desktop_app/utils/app_theme.py

"""
Single source of truth for the main app UI theme.

Goal:
- Clean modern light UI
- No accidental gray strips behind text
- Standard objectNames:
    title, Card, CardTitle, CardValue, primaryBtn, muted
"""

def load_app_theme() -> str:
    return """
/* =========================================================
   GLOBAL RESET / BASE
   ========================================================= */

QWidget {
    font-family: "Segoe UI", "Inter", Arial, sans-serif;
    font-size: 13px;
    color: #0F172A;
    background: #F6F8FC;
}

/* Prevent gray strips behind labels */
QLabel {
    background: transparent;
}

QAbstractButton, QToolButton {
    background: transparent;
}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background: #FFFFFF;
    border: 1px solid #D7DEEE;
    border-radius: 10px;
    padding: 8px 10px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QComboBox:focus, QSpinBox:focus {
    border: 1px solid #8CAFFF;
    background: #FFFFFF;
}

/* =========================================================
   TYPOGRAPHY HELPERS
   ========================================================= */

QLabel#title {
    font-size: 24px;
    font-weight: 900;
    color: #0A2A83;
}

QLabel#muted, QLabel.muted {
    font-size: 11px;
    color: rgba(15, 23, 42, 0.55);
}

/* =========================================================
   CARD SYSTEM
   ========================================================= */

QFrame#Card,
QFrame.Card {
    background: #FFFFFF;
    border: 1px solid #E2E8F5;
    border-radius: 14px;
}

QLabel#CardTitle {
    font-size: 12px;
    font-weight: 800;
    color: rgba(15, 23, 42, 0.70);
}

QLabel#CardValue {
    font-size: 18px;
    font-weight: 900;
    color: #0A2A83;
}

/* =========================================================
   HEADER BAR
   ========================================================= */

QWidget#headerBar {
    background: #FFFFFF;
    border-bottom: 1px solid #E6EAF3;
}

QLabel#headerTitle {
    font-size: 20px;
    font-weight: 900;
    color: #0A2A83;
}

QPushButton#menuBtn {
    background: #F4F7FF;
    border: 1px solid #DEE6FF;
    border-radius: 10px;
}

QPushButton#menuBtn:hover {
    background: #EAF0FF;
}

QLineEdit#searchBox {
    padding-left: 12px;
    font-size: 13px;
    border-radius: 12px;
    border: 1px solid #D7DEEE;
    background: #F8FAFF;
}

QLineEdit#searchBox:focus {
    border: 1px solid #8CAFFF;
    background: #FFFFFF;
}

QToolButton#profileBtn {
    background: #0A2A83;
    color: white;
    border-radius: 10px;
    font-weight: 800;
    font-size: 12px;
}

QToolButton#profileBtn:hover {
    background: #153AAB;
}

QMenu {
    background: #FFFFFF;
    border: 1px solid #CDD5EA;
    border-radius: 10px;
    padding: 6px 0;
}

QMenu::item {
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 600;
}

QMenu::item:selected {
    background: #EEF3FF;
}

/* =========================================================
   SIDEBAR
   ========================================================= */

QWidget#sidebar {
    background: #FFFFFF;
    border-right: 1px solid #E6EAF3;
}

QFrame#sidebarBrandCard {
    background: #F6F8FF;
    border: 1px solid #E3E9FF;
    border-radius: 14px;
}

QLabel#sidebarBrand,
QLabel#sidebarBrandSub,
QLabel#sidebarSection,
QLabel#sidebarName,
QLabel#sidebarRole {
    background: transparent;
}

QListWidget#sidebarMenu {
    border: none;
    outline: none;
    background: transparent;
}

QListWidget#sidebarMenu::item {
    margin-left: 2px;
    padding-left: 12px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 600;
    height: 40px;
    color: #23324D;
    background: transparent;
}

QListWidget#sidebarMenu::item:hover {
    background: #EEF3FF;
}

QListWidget#sidebarMenu::item:selected {
    background: #0A2A83;
    color: #FFFFFF;
}

QListWidget#sidebarMenu::item:disabled {
    color: rgba(35, 50, 77, 0.28);
    background: transparent;
}

QFrame#sidebarFooter {
    background: #F8FAFF;
    border: 1px solid #E5EBFF;
    border-radius: 14px;
    min-height: 72px;
}

QLabel#sidebarAvatar {
    background: #0A2A83;
    color: white;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 800;
}

/* =========================================================
   BUTTON SYSTEM
   ========================================================= */

QPushButton {
    border-radius: 10px;
    padding: 8px 12px;
    font-weight: 600;
    border: 1px solid #D7DEEE;
    background: #FFFFFF;
}

QPushButton:hover {
    background: #F4F7FF;
}

QPushButton#primaryBtn {
    background: #0A2A83;
    color: #FFFFFF;
    border: 1px solid #0A2A83;
}

QPushButton#primaryBtn:hover {
    background: #153AAB;
    border: 1px solid #153AAB;
}

QPushButton:disabled {
    background: #F2F4F8;
    color: rgba(0, 0, 0, 0.35);
    border: 1px solid #E5E9F2;
}

/* =========================================================
   TABLES
   ========================================================= */

QTableWidget {
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E2E8F5;
    gridline-color: #E6ECF7;
    alternate-background-color: #F8FAFF;
}

QHeaderView::section {
    background-color: #F4F6FD;
    padding: 6px;
    border: none;
    font-weight: 700;
    font-size: 12px;
}

QTableWidget::item {
    padding: 6px;
    background: transparent;
}

/* ✅ Selection fix (prevents white-out) */
QTableWidget::item:selected {
    background: #0A2A83;
    color: #FFFFFF;
}

QTableWidget::item:selected:active {
    background: #0A2A83;
    color: #FFFFFF;
}

QTableWidget::item:hover {
    background: #EEF3FF;
}

/* =========================================================
   SCROLLBARS
   ========================================================= */

QScrollBar:vertical {
    width: 10px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: #D9E2F5;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #C9D5F0;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
