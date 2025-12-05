# desktop_app/utils/styles.py
"""
Small helper styles used by dialogs and legacy code.
Used by login and MFA dialogs.
"""

def get_dialog_style():
    return r"""
QDialog {
    background: #F7F8FA;
    color: #0F172A;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
QLabel { color: #0F172A; }
QLineEdit {
    background: white;
    border: 1px solid rgba(15,23,42,0.06);
    border-radius: 6px;
    padding: 8px;
}
QPushButton {
    background: #4b6cff;
    color: white;
    border-radius: 8px;
    padding: 8px 12px;
}
QPushButton#ghost {
    background: transparent;
    color: #0F172A;
    border: 1px solid rgba(15,23,42,0.06);
}
"""
