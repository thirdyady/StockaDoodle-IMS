def load_light_theme():
    return """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    background-color: #FBFDFF;
}

/* TITLE */
QLabel[class="pageTitle"] {
    font-size: 26px;
    font-weight: 600;
    margin-bottom: 14px;
}

/* KPI */
#KPI {
    background: #FFFFFF;
    border-radius: 18px;
    border: 1px solid #E6E6E8;
}

#KPI #value {
    font-size: 26px;
    font-weight: 700;
    color: #1A1A1A;
}

/* ACTIVITY BOX */
#activityBox {
    background: #FFFFFF;
    border-radius: 18px;
    border: 1px solid #E6E6E8;
}

#activityTitle {
    font-size: 15px;
    font-weight: bold;
    margin-bottom: 6px;
    color: #222;
}

/* SIDEBAR */
#sideBar {
    background-color: #FFFFFF;
    border-right: 1px solid #E8E8E8;
}

/* SIDEBAR ITEMS */
#sidebarMenu::item {
    height: 40px;
    font-size: 14px;
    padding-left: 12px;
    border-radius: 8px;
}

#sidebarMenu::item:selected {
    background-color: #005EFF;
    color: white;
    font-weight: 600;
}
"""
