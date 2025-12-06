# desktop_app/utils/styles.py
"""
Small helper styles used by dialogs and legacy code.
Used by login and MFA dialogs.
"""

def get_dialog_style() -> str:
    return r"""
QDialog, QWidget#loginWindow {
    background: #F7F8FA;
    color: #0F172A;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QLabel {
    color: #0F172A;
}

QLabel#loginTitle {
    font-size: 22px;
    font-weight: 700;
}

QLabel#loginSubtitle {
    font-size: 13px;
    color: rgba(15,23,42,0.70);
}

QLabel#loginFooter {
    font-size: 11px;
    color: rgba(15,23,42,0.45);
}

QLineEdit#loginInput {
    background: white;
    border: 1px solid rgba(15,23,42,0.08);
    border-radius: 8px;
    padding: 8px 10px;
}

QPushButton#loginBtn {
    background: #4B6CFF;
    color: white;
    border-radius: 10px;
    padding: 10px 12px;
    font-weight: 600;
    border: none;
}

QPushButton#loginBtn:disabled {
    background: #9CA3AF;
}

QPushButton#ghost {
    background: transparent;
    color: #0F172A;
    border-radius: 8px;
    padding: 8px 12px;
    border: 1px solid rgba(15,23,42,0.06);
}
"""
