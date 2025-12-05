# desktop_app/utils/style_presets.py
"""
Style preset helper functions to satisfy utils.__init__.__all__
and keep compatibility with your classmate's design.

These wrap the global theme and provide per-component styles.
"""

from utils.theme import load_light_theme
from utils.styles import get_dialog_style as _base_dialog_style


def get_global_stylesheet():
    """
    Global app stylesheet. Right now we just reuse the light corporate theme.
    """
    return load_light_theme()


def get_dashboard_card_style():
    """
    Extra style you can apply to dashboard cards if needed.
    """
    return """
    QFrame[objectName='dashboardCard'] {
        background: white;
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,0.08);
        padding: 12px;
    }
    """


def get_product_card_style():
    return """
    QFrame[objectName='productCard'] {
        background: #FFFFFF;
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,0.10);
        padding: 12px;
    }
    """


def get_category_card_style():
    return """
    QFrame[objectName='categoryCard'] {
        background: #F9FAFB;
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,0.06);
        padding: 10px 12px;
    }
    """


def get_dialog_style():
    """
    Use the existing dialog style from utils/styles.py so MFA/login stay consistent.
    """
    return _base_dialog_style()


def get_header_bar_style():
    return """
    QWidget#headerBar {
        background: #FFFFFF;
        border-bottom: 1px solid rgba(0,0,0,0.06);
    }
    """


def get_title_bar_style():
    return """
    QLabel.title {
        font-size: 26px;
        font-weight: 700;
        color: #0F172A;
    }
    """


def get_loading_spinner_style():
    return """
    QLabel[objectName='spinner'] {
        qproperty-alignment: AlignCenter;
    }
    """


def get_modern_card_style():
    return """
    QFrame[objectName='modernCard'] {
        background: white;
        border-radius: 12px;
        padding: 12px;
        border: 1px solid rgba(0,0,0,0.08);
    }
    QLabel.cardTitle {
        color: #64748B;
        font-weight: 600;
    }
    QLabel.cardValue {
        color: #0F172A;
        font-weight: 800;
        font-size: 16px;
    }
    """


def get_badge_style():
    return """
    QLabel[objectName='badge'] {
        background: #EEF2FF;
        color: #4C6EF5;
        padding: 3px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
    }
    """


def apply_table_styles(table):
    """
    Apply a simple, safe table style. If anything goes wrong it fails silently.
    """
    try:
        table.setStyleSheet("""
        QHeaderView::section {
            background: #F3F4F6;
            border: none;
            padding: 6px 8px;
            font-weight: 600;
        }
        QTableWidget {
            gridline-color: rgba(0,0,0,0.08);
            background: white;
            selection-background-color: #DBEAFE;
        }
        """)
    except Exception:
        # don't crash the app if someone passes a weird object
        pass
