# desktop_app/utils/theme.py

def load_light_theme() -> str:
    return """
/* GLOBAL */
QWidget {
    background: #F8FAFC;
    color: #0F172A;
    font-family: 'Segoe UI';
    font-size: 13px;
}

/* PAGE TITLES */
QLabel[class="pageTitle"] {
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 4px;
}

/* HEADER BAR */
QWidget#headerBar {
    background: #FFFFFF;
    border-bottom: 1px solid rgba(0,0,0,0.07);
}

QLineEdit#headerSearch {
    background: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.18);
    border-radius: 8px;
    padding: 6px 10px;
}

QPushButton#avatarBtn {
    background: #0F172A;
    color: white;
    border-radius: 18px;
    min-width: 36px;
    min-height: 36px;
    font-weight: 600;
}

/* SIDEBAR */
QWidget#sideBar {
    background: #FFFFFF;
    border-right: 1px solid rgba(0,0,0,0.08);
}

QLabel#brand {
    font-size: 16px;
    font-weight: 700;
    color: #0F172A;
}

QListWidget#sidebarMenu {
    background: transparent;
    border: none;
}

QListWidget#sidebarMenu::item {
    padding: 10px;
    margin: 4px 8px;
    color: rgba(15,23,42,0.70);
    border-radius: 8px;
}

QListWidget#sidebarMenu::item:selected {
    background: #2463EB;
    color: white;
    font-weight: 600;
}

/* KPI CARDS */
QFrame#KPI {
    background: #FFFFFF;
    border-radius: 18px;
    border: 1px solid #E2E8F0;
}

QFrame#IconBubble {
    background: #E5EBFB;
    border-radius: 12px;
}

/* KPI LABELS */
QLabel#kpiTitle {
    font-size: 12px;
    color: rgba(15,23,42,0.60);
}

QLabel#kpiValue {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
}

/* ACTIVITY CARD */
QFrame#activityBox {
    background: #FFFFFF;
    border-radius: 18px;
    border: 1px solid #E2E8F0;
}

QLabel#activityTitle {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 6px;
}

/* Activity list */
QListWidget#activityList {
    background: #F9FAFF;
    border-radius: 10px;
    border: 1px solid #DFE8FF;
    padding: 6px 10px;
}

QListWidget#activityList::item {
    padding: 6px 4px;
    color: #0F172A;
}

QListWidget#activityList::item:selected {
    background: rgba(36,99,235,0.18);
    border-left: 3px solid #2463EB;
}
"""
