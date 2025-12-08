# core/pdf_report_generator.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, PageBreak, KeepTogether, HRFlowable
)
from datetime import datetime
import os
from io import BytesIO

from utils.pdf_styles import (
    PDFColors, PDFStyles, PDFTableStyles,
    PDFLayoutHelpers, PDFBranding
)


def _footer_canvas(canvas, doc):
    """Draw footer on every page at the bottom"""
    canvas.saveState()

    footer_y = doc.bottomMargin - 0.3 * inch

    canvas.setStrokeColor(PDFColors.GOLD_ACCENT)
    canvas.setLineWidth(0.5)
    canvas.line(
        doc.leftMargin,
        footer_y + 0.2 * inch,
        doc.width + doc.leftMargin,
        footer_y + 0.2 * inch
    )

    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(PDFColors.MEDIUM_GRAY)
    canvas.drawCentredString(
        (doc.width + doc.leftMargin + doc.rightMargin) / 2,
        footer_y,
        f"Generated on {timestamp}"
    )

    footer_text = f"{PDFBranding.COMPANY_NAME} | {PDFBranding.BRANCH_NAME}"
    canvas.drawCentredString(
        (doc.width + doc.leftMargin + doc.rightMargin) / 2,
        footer_y - 0.15 * inch,
        footer_text
    )

    canvas.restoreState()


class PDFReportGenerator:
    """
    Professional PDF report generator for all 7 StockaDoodle reports
    """

    def __init__(self):
        self.styles = self._init_styles()

    def _init_styles(self):
        """Initialize all paragraph styles"""
        return {
            'title': PDFStyles.get_title_style(),
            'subtitle': PDFStyles.get_subtitle_style(),
            'section': PDFStyles.get_section_header_style(),
            'body': PDFStyles.get_body_style(),
            'footer': PDFStyles.get_footer_style(),
            'metric_label': PDFStyles.get_metric_label_style(),
            'metric_value': PDFStyles.get_metric_value_style()
        }

    def _add_professional_header(self, elements):
        """Add professional header with logo and company branding"""
        logo_paths = [
            PDFBranding.LOGO_PATH,
            PDFBranding.LOGO_FALLBACK_PATH,
            "../desktop_app/assets/icons/stockadoodle-transparent.png",
            "../../desktop_app/assets/icons/stockadoodle-transparent.png",
        ]

        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    logo = Image(logo_path, width=1.5 * inch, height=1.5 * inch)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(PDFLayoutHelpers.create_spacer(0.1))
                    break
                except Exception:
                    continue

        company_para = Paragraph(
            f"<b>{PDFBranding.COMPANY_NAME}</b>",
            self.styles['title']
        )
        elements.append(company_para)

        branch_para = Paragraph(
            f'<font color="{PDFColors.MEDIUM_GRAY}">{PDFBranding.BRANCH_NAME}</font>',
            self.styles['subtitle']
        )
        elements.append(branch_para)

        elements.append(PDFLayoutHelpers.create_gold_border_line())
        elements.append(PDFLayoutHelpers.create_spacer(0.25))

    def _add_report_title(self, elements, title, subtitle=None):
        """Add report-specific title section"""
        elements.append(Paragraph(title, self.styles['title']))
        if subtitle:
            elements.append(Paragraph(subtitle, self.styles['subtitle']))
        elements.append(PDFLayoutHelpers.create_spacer(0.2))

    def _add_professional_footer(self, elements):
        """Footer spacing (actual footer drawn via canvas callback)"""
        elements.append(PDFLayoutHelpers.create_spacer(0.5))

    def _create_summary_box(self, summary_data):
        """Create styled summary metrics box"""
        data = [[label, value] for label, value in summary_data.items()]
        table = Table(data, colWidths=[3 * inch, 2.5 * inch])
        table.setStyle(PDFTableStyles.get_summary_table_style())
        return table

    def _create_data_table(self, data, col_widths=None):
        """Create professional data table"""
        table = Table(data, colWidths=col_widths)
        table.setStyle(PDFTableStyles.get_standard_table_style())
        return table

    # ================================================================
    # REPORT 1
    # ================================================================
    def generate_sales_performance_report(self, report_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            topMargin=0.5 * inch,
            bottomMargin=0.8 * inch,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch
        )
        elements = []

        self._add_professional_header(elements)

        start_date = report_data.get('date_range', {}).get('start')
        end_date = report_data.get('date_range', {}).get('end')
        date_range = f"{start_date} to {end_date}" if start_date and end_date else "Not specified"

        self._add_report_title(elements, "Detailed Sales Transaction Report", f"Report Period: {date_range}")

        elements.append(Paragraph("Summary", self.styles['section']))

        summary = report_data.get('summary', {})
        summary_data = {
            'Total Revenue': f"${float(summary.get('total_income', 0) or 0):,.2f}",
            'Total Quantity Sold': f"{int(summary.get('total_quantity_sold', 0) or 0):,}",
            'Total Transactions': f"{int(summary.get('total_transactions', 0) or 0):,}"
        }

        elements.append(self._create_summary_box(summary_data))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))

        if report_data.get('sales'):
            elements.append(Paragraph("Sales Details", self.styles['section']))

            sales_data = [['Sale ID', 'Date', 'Product', 'Qty', 'Price', 'Retailer']]

            for sale in report_data['sales'][:50]:
                sales_data.append([
                    str(sale.get('sale_id', 'N/A')),
                    (sale.get('date', 'N/A') or 'N/A')[:10],
                    (sale.get('product_name', 'N/A') or 'N/A')[:25],
                    str(sale.get('quantity_sold', 0) or 0),
                    f"${float(sale.get('total_price', 0) or 0):,.2f}",
                    (sale.get('retailer_name', 'N/A') or 'N/A')[:20]
                ])

            sales_table = self._create_data_table(
                sales_data,
                col_widths=[0.7 * inch, 1 * inch, 2 * inch, 0.6 * inch, 1 * inch, 1.5 * inch]
            )
            elements.append(sales_table)

        self._add_professional_footer(elements)

        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer

    # ================================================================
    # REPORT 2
    # ================================================================
    def generate_category_distribution_report(self, report_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            topMargin=0.5 * inch, bottomMargin=0.8 * inch,
            leftMargin=0.75 * inch, rightMargin=0.75 * inch
        )
        elements = []

        self._add_professional_header(elements)
        self._add_report_title(elements, "Category Distribution Report")

        summary = report_data.get('summary', {})
        summary_text = {
            'Total Categories': str(summary.get('total_categories', 0)),
            'Total Stock': f"{int(summary.get('total_stock', 0) or 0):,} units"
        }
        elements.append(Paragraph("Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))

        elements.append(Paragraph("Category Breakdown", self.styles['section']))
        cat_data = [['Category', 'Products', 'Stock Quantity', 'Share']]

        for cat in report_data.get('categories', []):
            cat_data.append([
                cat.get('category_name', 'Unknown'),
                str(cat.get('number_of_products', 0)),
                f"{int(cat.get('total_stock_quantity', 0) or 0):,}",
                f"{float(cat.get('percentage_share', 0) or 0):.1f}%"
            ])

        cat_table = self._create_data_table(
            cat_data,
            col_widths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch]
        )
        elements.append(cat_table)

        self._add_professional_footer(elements)

        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer

    # ================================================================
    # REPORT 3
    # ================================================================
    def generate_retailer_performance_report(self, report_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            topMargin=0.5 * inch, bottomMargin=0.8 * inch,
            leftMargin=0.75 * inch, rightMargin=0.75 * inch
        )
        elements = []

        self._add_professional_header(elements)
        self._add_report_title(elements, "Retailer Performance Report")

        summary = report_data.get('summary', {})
        summary_text = {
            'Total Retailers': str(summary.get('total_retailers', 0)),
            'Active Today': str(summary.get('active_today', 0))
        }

        elements.append(Paragraph("Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))

        elements.append(Paragraph("Performance Metrics", self.styles['section']))
        ret_data = [['Retailer', 'Daily Quota', "Today's Sales", 'Progress', 'Streak', 'Total Sales']]

        for ret in report_data.get('retailers', []):
            ret_data.append([
                (ret.get('retailer_name', 'Unknown') or 'Unknown')[:25],
                f"${float(ret.get('daily_quota', 0) or 0):,.2f}",
                f"${float(ret.get('current_sales', 0) or 0):,.2f}",
                f"{float(ret.get('quota_progress', 0) or 0):.1f}%",
                str(ret.get('streak_count', 0) or 0),
                f"${float(ret.get('total_sales', 0) or 0):,.2f}"
            ])

        ret_table = self._create_data_table(
            ret_data,
            col_widths=[2 * inch, 1 * inch, 1 * inch, 0.8 * inch, 0.7 * inch, 1 * inch]
        )
        elements.append(ret_table)

        self._add_professional_footer(elements)

        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer

    # ================================================================
    # REPORT 4
    # ================================================================
    def generate_alerts_report(self, report_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            topMargin=0.5 * inch, bottomMargin=0.8 * inch,
            leftMargin=0.75 * inch, rightMargin=0.75 * inch
        )
        elements = []

        self._add_professional_header(elements)
        self._add_report_title(elements, "Low-Stock & Expiration Alert Report")

        summary = report_data.get('summary', {})
        summary_text = {
            'Total Alerts': str(summary.get('total_alerts', 0)),
            'Critical': str(summary.get('critical_alerts', 0)),
            'Warning': str(summary.get('warning_alerts', 0))
        }

        elements.append(Paragraph("Alert Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))

        elements.append(Paragraph("Alert Details", self.styles['section']))
        alert_data = [['Product', 'Current Stock', 'Min Level', 'Expiration', 'Status', 'Severity']]

        for alert in report_data.get('alerts', []):
            alert_data.append([
                (alert.get('product_name', 'Unknown') or 'Unknown')[:30],
                str(alert.get('current_stock', 0) or 0),
                str(alert.get('min_stock_level', 0) or 0),
                alert.get('expiration_date') or 'N/A',
                alert.get('alert_status', ''),
                alert.get('severity', '')
            ])

        alert_table = self._create_data_table(
            alert_data,
            col_widths=[2 * inch, 1 * inch, 0.9 * inch, 1 * inch, 1.5 * inch, 0.8 * inch]
        )
        elements.append(alert_table)

        self._add_professional_footer(elements)

        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer

    # ================================================================
    # REPORT 5
    # ================================================================
    def generate_managerial_activity_report(self, report_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            topMargin=0.5 * inch, bottomMargin=0.8 * inch,
            leftMargin=0.75 * inch, rightMargin=0.75 * inch
        )
        elements = []

        self._add_professional_header(elements)

        dr = report_data.get('date_range', {})
        date_range = f"{dr.get('start', '')} to {dr.get('end', '')}".strip()

        self._add_report_title(elements, "Managerial Activity Log Report", f"Report Period: {date_range}")

        summary = report_data.get('summary', {})
        summary_text = {
            'Total Actions': str(summary.get('total_actions', 0)),
            'Unique Managers': str(summary.get('unique_managers', 0))
        }

        elements.append(Paragraph("Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))

        elements.append(Paragraph("Activity Log", self.styles['section']))
        log_data = [['Log ID', 'Product', 'Action', 'Manager', 'Date/Time']]

        for log in report_data.get('logs', [])[:100]:
            log_data.append([
                str(log.get('log_id', '')),
                (log.get('product_name', 'Unknown') or 'Unknown')[:25],
                log.get('action_performed', ''),
                (log.get('manager_name', 'Unknown') or 'Unknown')[:20],
                (log.get('date_time', '') or '')[:16]
            ])

        log_table = self._create_data_table(
            log_data,
            col_widths=[0.7 * inch, 2 * inch, 1.3 * inch, 1.5 * inch, 1.5 * inch]
        )
        elements.append(log_table)

        self._add_professional_footer(elements)

        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer

    # ================================================================
    # REPORT 6
    # ================================================================
    def generate_transactions_report(self, report_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            topMargin=0.5 * inch, bottomMargin=0.8 * inch,
            leftMargin=0.75 * inch, rightMargin=0.75 * inch
        )
        elements = []

        self._add_professional_header(elements)

        # ✅ FIX: Correct report title
        self._add_report_title(elements, "Detailed Sales Transaction Report")

        summary = report_data.get('summary', {})
        summary_text = {
            'Total Revenue': f"${float(summary.get('total_revenue', 0) or 0):,.2f}",
            'Total Transactions': f"{int(summary.get('total_transactions', 0) or 0):,}",
            'Total Sales Count': f"{int(summary.get('total_sales_count', 0) or 0):,}",
            'Total Items Sold': f"{int(summary.get('total_items_sold', 0) or 0):,}"
        }

        elements.append(Paragraph("Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))

        dr = report_data.get('date_range', {})
        start_date = dr.get('start')
        end_date = dr.get('end')
        date_range = f"{start_date} to {end_date}" if start_date and end_date else "Not Specified"

        elements.append(Paragraph(f"Report Period: {date_range}", self.styles['section']))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))

        elements.append(Paragraph("Sales Breakdown", self.styles['section']))
        sales_data = [['Sale ID', 'Product', 'Brand', 'Qty', 'Unit Price', 'Line Total', 'Retailer']]

        # ✅ Safety: cap rows
        for transaction in (report_data.get('transactions', [])[:100]):
            sales_data.append([
                str(transaction.get('sale_id', '')),
                (transaction.get('product_name', 'Unknown') or 'Unknown')[:30],
                (transaction.get('product_brand', '') or '')[:15],
                str(transaction.get('quantity_sold', 0) or 0),
                f"${float(transaction.get('unit_price', 0) or 0):.2f}",
                f"${float(transaction.get('line_total', 0) or 0):.2f}",
                (transaction.get('retailer_name', 'Unknown') or 'Unknown')[:25]
            ])

        sales_table = self._create_data_table(
            sales_data,
            col_widths=[0.8 * inch, 2 * inch, 1 * inch, 0.7 * inch, 1 * inch, 1 * inch, 1.5 * inch]
        )
        elements.append(sales_table)

        self._add_professional_footer(elements)

        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer

    # ================================================================
    # REPORT 7
    # ================================================================
    def generate_user_accounts_report(self, report_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            topMargin=0.5 * inch, bottomMargin=0.8 * inch,
            leftMargin=0.75 * inch, rightMargin=0.75 * inch
        )
        elements = []

        self._add_professional_header(elements)
        self._add_report_title(elements, "User Accounts Report")

        summary = report_data.get('summary', {})
        summary_text = {
            'Total Users': str(summary.get('total_users', 0)),
            'Admins': str(summary.get('admins', 0)),
            'Managers': str(summary.get('managers', 0)),
            'Retailers': str(summary.get('retailers', 0))
        }

        elements.append(Paragraph("Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))

        elements.append(Paragraph("User Details", self.styles['section']))
        user_data = [['User ID', 'Username', 'Full Name', 'Role', 'Status']]

        for user in report_data.get('users', []):
            user_data.append([
                str(user.get('user_id', '')),
                (user.get('username', '') or '')[:20],
                (user.get('full_name', '') or '')[:25],
                (user.get('role', '') or '').capitalize(),
                user.get('account_status', 'Unknown')
            ])

        user_table = self._create_data_table(
            user_data,
            col_widths=[0.8 * inch, 1.5 * inch, 2 * inch, 1.2 * inch, 1.2 * inch]
        )
        elements.append(user_table)

        self._add_professional_footer(elements)

        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer
