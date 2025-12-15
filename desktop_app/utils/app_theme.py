# desktop_app/utils/app_theme.py

"""
Single source of truth for the main app UI theme.

Goal:
- Clean modern light UI
- No accidental gray strips behind text
- Standard objectNames:
    title, Card, CardTitle, CardValue, primaryBtn, secondaryBtn, ghost, muted

NOTE:
- This theme is GLOBAL.
- To avoid breaking other pages, we only add "compact table buttons" under QTableWidget scope.
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

QLabel { background: transparent; }
QAbstractButton, QToolButton { background: transparent; }

QFrame { background: transparent; }

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

/* SpinBox arrows feel tighter */
QSpinBox::up-button, QSpinBox::down-button {
    width: 18px;
    border: none;
}
QSpinBox::up-arrow, QSpinBox::down-arrow {
    width: 8px;
    height: 8px;
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
   BUTTON SYSTEM
   ========================================================= */

QPushButton {
    border-radius: 10px;
    padding: 8px 12px;
    font-weight: 700;
    border: 1px solid #D7DEEE;
    background: #FFFFFF;
    min-height: 34px;
}

QPushButton:hover {
    background: #F4F7FF;
}

QPushButton#primaryBtn {
    background: #0A2A83;
    color: #FFFFFF;
    border: 1px solid #0A2A83;
    min-height: 36px;
}

QPushButton#primaryBtn:hover {
    background: #153AAB;
    border: 1px solid #153AAB;
}

QPushButton#secondaryBtn {
    background: #EEF3FF;
    color: #0A2A83;
    border: 1px solid #CFE0FF;
    min-height: 34px;
}

QPushButton#secondaryBtn:hover {
    background: #E3ECFF;
    border: 1px solid #BFD6FF;
}

QPushButton#ghost {
    background: transparent;
    color: #0F172A;
    border: 1px solid rgba(15,23,42,0.10);
    min-height: 34px;
}

QPushButton#ghost:hover {
    background: #F4F7FF;
}

QPushButton:disabled {
    background: #F2F4F8;
    color: rgba(0, 0, 0, 0.35);
    border: 1px solid #E5E9F2;
}

/* =========================================================
   COMPACT BUTTONS INSIDE TABLES ONLY
   ========================================================= */

QTableWidget QPushButton {
    padding: 4px 10px;
    min-height: 28px;
    max-height: 28px;
    margin: 0px;
    border-radius: 8px;
    font-weight: 700;
}

/* Keep your variants compact too */
QTableWidget QPushButton#primaryBtn,
QTableWidget QPushButton#secondaryBtn,
QTableWidget QPushButton#ghost {
    padding: 4px 10px;
    min-height: 28px;
    max-height: 28px;
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
    padding: 8px;
    border: none;
    font-weight: 800;
    font-size: 12px;
}

QTableWidget::item {
    padding: 8px;
    background: transparent;
}

/* Selection */
QTableWidget::item:selected,
QTableWidget::item:selected:active {
    background: #0A2A83;
    color: #FFFFFF;
}

QTableWidget::item:hover {
    background: #EEF3FF;
}

/* =========================================================
   MENUS
   ========================================================= */

QMenu {
    background: #FFFFFF;
    border: 1px solid #CDD5EA;
    border-radius: 10px;
    padding: 6px 0;
}

QMenu::item {
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 700;
}

QMenu::item:selected {
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

/* ✅ Horizontal scrollbar styling too */
QScrollBar:horizontal {
    height: 10px;
    background: transparent;
}
QScrollBar::handle:horizontal {
    background: #D9E2F5;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #C9D5F0;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""
