"""
Professional PDF Report Styling Utilities for StockaDoodle IMS
Corporate luxury design with navy blue, purple, and gold accents
"""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import PageBreak, Spacer
from reportlab.lib.units import inch


class PDFColors:
    """Corporate color palette - Enhanced for better visual appeal"""
    # Primary colors
    NAVY_DARK = colors.HexColor('#1E293B')  # Darker navy for better contrast
    PURPLE_RICH = colors.HexColor('#6C5CE7')  # Primary brand purple
    GOLD_ACCENT = colors.HexColor('#FDCB6E')  # Gold accent
    
    # Secondary colors
    WHITE = colors.white
    LIGHT_GRAY = colors.HexColor('#F1F5F9')  # Lighter gray for better readability
    MEDIUM_GRAY = colors.HexColor('#64748B')  # Medium gray for subtitles
    DARK_GRAY = colors.HexColor('#334155')  # Dark gray for body text
    
    # Status colors
    SUCCESS_GREEN = colors.HexColor('#10B981')
    WARNING_ORANGE = colors.HexColor('#F59E0B')
    CRITICAL_RED = colors.HexColor('#EF4444')
    
    # Table colors
    HEADER_BG = NAVY_DARK
    ROW_ALT_BG = LIGHT_GRAY
    BORDER_COLOR = colors.HexColor('#CBD5E1')  # Lighter border


class PDFStyles:
    """Reusable paragraph styles"""
    
    @staticmethod
    def get_title_style():
        """Main report title - large, centered, navy with better spacing"""
        return ParagraphStyle(
            name='ReportTitle',
            fontName='Helvetica-Bold',
            fontSize=28,
            textColor=PDFColors.NAVY_DARK,
            alignment=TA_CENTER,
            spaceAfter=12,
            spaceBefore=8,
            leading=32
        )
    
    @staticmethod
    def get_subtitle_style():
        """Report subtitle - medium, centered, purple with better styling"""
        return ParagraphStyle(
            name='ReportSubtitle',
            fontName='Helvetica',
            fontSize=13,
            textColor=PDFColors.MEDIUM_GRAY,
            alignment=TA_CENTER,
            spaceAfter=16,
            spaceBefore=4,
            leading=16
        )
    
    @staticmethod
    def get_section_header_style():
        """Section headers - bold, left-aligned with orange background"""
        return ParagraphStyle(
            name='SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=PDFColors.NAVY_DARK,
            alignment=TA_LEFT,
            spaceAfter=12,
            spaceBefore=16,
            backColor=PDFColors.GOLD_ACCENT,
            borderPadding=(8, 4, 8, 4),
            leading=18
        )
    
    @staticmethod
    def get_body_style():
        """Normal body text"""
        return ParagraphStyle(
            name='BodyText',
            fontName='Helvetica',
            fontSize=11,
            textColor=PDFColors.DARK_GRAY,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14
        )
    
    @staticmethod
    def get_footer_style():
        """Footer text - small, centered, gray"""
        return ParagraphStyle(
            name='FooterText',
            fontName='Helvetica',
            fontSize=9,
            textColor=PDFColors.MEDIUM_GRAY,
            alignment=TA_CENTER,
            spaceAfter=4
        )
    
    @staticmethod
    def get_metric_label_style():
        """Metric labels in summary boxes"""
        return ParagraphStyle(
            name='MetricLabel',
            fontName='Helvetica',
            fontSize=10,
            textColor=PDFColors.MEDIUM_GRAY,
            alignment=TA_LEFT
        )
    
    @staticmethod
    def get_metric_value_style():
        """Metric values in summary boxes"""
        return ParagraphStyle(
            name='MetricValue',
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=PDFColors.NAVY_DARK,
            alignment=TA_LEFT
        )


class PDFTableStyles:
    """Reusable table styling configurations"""
    
    @staticmethod
    def get_standard_table_style():
        """Standard data table style with alternating rows"""
        from reportlab.platypus import TableStyle
        
        return TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), PDFColors.HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), PDFColors.WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), PDFColors.WHITE),
            ('TEXTCOLOR', (0, 1), (-1, -1), PDFColors.DARK_GRAY),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PDFColors.WHITE, PDFColors.ROW_ALT_BG]),
            
            # Grid lines
            ('GRID', (0, 0), (-1, -1), 0.5, PDFColors.BORDER_COLOR),
            ('LINEBELOW', (0, 0), (-1, 0), 2, PDFColors.GOLD_ACCENT),
        ])
    
    @staticmethod
    def get_summary_table_style():
        """Summary metrics table style - cleaner design"""
        from reportlab.platypus import TableStyle
        
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PDFColors.WHITE),
            ('TEXTCOLOR', (0, 0), (-1, -1), PDFColors.DARK_GRAY),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 11),
            ('FONTSIZE', (1, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, PDFColors.BORDER_COLOR),
            ('LINEBELOW', (0, 0), (-1, 0), 2, PDFColors.GOLD_ACCENT),
        ])


class PDFLayoutHelpers:
    """Helper functions for consistent layout"""
    
    @staticmethod
    def create_spacer(height_inches=0.2):
        """Create a spacer of specified height"""
        return Spacer(0, height_inches * inch)
    
    @staticmethod
    def create_section_divider():
        """Create a decorative section divider"""
        from reportlab.platypus import HRFlowable
        return HRFlowable(
            width="100%",
            thickness=1,
            color=PDFColors.GOLD_ACCENT,
            spaceBefore=15,
            spaceAfter=15
        )
    
    @staticmethod
    def create_gold_border_line():
        """Create thin gold border line"""
        from reportlab.platypus import HRFlowable
        return HRFlowable(
            width="100%",
            thickness=0.5,
            color=PDFColors.GOLD_ACCENT,
            spaceBefore=5,
            spaceAfter=5
        )


class PDFBranding:
    """Company branding constants"""
    COMPANY_NAME = "StockaDoodle Inventory Management System"
    BRANCH_NAME = "QuickMart – Quezon Branch"
    LOGO_PATH = "desktop_app/assets/icons/stockadoodle-transparent.png"
    LOGO_FALLBACK_PATH  = "desktop_app/assets/icons/stockadoodle-white.ico"
