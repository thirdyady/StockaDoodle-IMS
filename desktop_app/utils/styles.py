# desktop_app/utils/styles.py
"""
Small helper styles used by dialogs and legacy code.
Used by login and MFA dialogs.
"""

def get_dialog_style() -> str:
    return r"""
QDialog, QWidget#loginWindow {
    background: #F7F9FC;
    color: #0F172A;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QLabel {
    color: #0F172A;
    background: transparent;
}

QLabel#loginTitle {
    font-size: 22px;
    font-weight: 800;
    color: #0B1B3B;
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
    border: 1px solid rgba(15,23,42,0.10);
    border-radius: 10px;
    padding: 10px 12px;
}

QPushButton#loginBtn {
    background: #0A2A83;
    color: white;
    border-radius: 12px;
    padding: 12px 12px;
    font-weight: 700;
    border: none;
}

QPushButton#loginBtn:hover {
    background: #143BAF;
}

QPushButton#loginBtn:disabled {
    background: #9CA3AF;
}

QPushButton#ghost {
    background: transparent;
    color: #0F172A;
    border-radius: 10px;
    padding: 8px 12px;
    border: 1px solid rgba(15,23,42,0.08);
}
"""
