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

from utils.pdf_styles import(
    PDFColors, PDFStyles, PDFTableStyles, 
    PDFLayoutHelpers, PDFBranding
)


def _footer_canvas(canvas, doc):
    """Draw footer on every page at the bottom"""
    canvas.saveState()
    
    # Calculate footer position (bottom of page)
    footer_y = doc.bottomMargin - 0.3 * inch
    
    # Draw gold divider line
    canvas.setStrokeColor(PDFColors.GOLD_ACCENT)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, footer_y + 0.2*inch, 
                doc.width + doc.leftMargin, footer_y + 0.2*inch)
    
    # Generation timestamp
    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(PDFColors.MEDIUM_GRAY)
    canvas.drawCentredString(
        (doc.width + doc.leftMargin + doc.rightMargin) / 2,
        footer_y,
        f"Generated on {timestamp}"
    )
    
    # Company footer
    footer_text = f"{PDFBranding.COMPANY_NAME} | {PDFBranding.BRANCH_NAME}"
    canvas.drawCentredString(
        (doc.width + doc.leftMargin + doc.rightMargin) / 2,
        footer_y - 0.15*inch,
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
    
    def _draw_header_background(self, canvas, doc):
        """Draw gradient header background (called on each page)"""
        canvas.saveState()
        
        # Draw navy to purple gradient background
        canvas.setFillColor(PDFColors.NAVY_DARK)
        canvas.rect(0, doc.height + doc.topMargin - 0.5*inch, 
                   doc.width + doc.leftMargin + doc.rightMargin, 
                   1*inch, fill=1, stroke=0)
        
        # Gold accent lines on left and right edges
        canvas.setStrokeColor(PDFColors.GOLD_ACCENT)
        canvas.setLineWidth(2)
        canvas.line(doc.leftMargin - 10, 0, 
                   doc.leftMargin - 10, doc.height + doc.topMargin)
        canvas.line(doc.width + doc.leftMargin + 10, 0, 
                   doc.width + doc.leftMargin + 10, doc.height + doc.topMargin)
        
        canvas.restoreState()
    
    def _add_professional_header(self, elements):
        """Add professional header with logo and company branding"""
        # Add company logo - try multiple paths
        logo_paths = [
            PDFBranding.LOGO_PATH,
            PDFBranding.LOGO_FALLBACK_PATH,
            "../desktop_app/assets/icons/stockadoodle-transparent.png",
            "../../desktop_app/assets/icons/stockadoodle-transparent.png",
        ]
        
        logo_added = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(PDFLayoutHelpers.create_spacer(0.1))
                    logo_added = True
                    break
                except Exception as e:
                    print(f"Logo loading failed from {logo_path}: {e}")
                    continue
        
        # Company name
        company_para = Paragraph(
            f"<b>{PDFBranding.COMPANY_NAME}</b>", 
            self.styles['title']
        )
        elements.append(company_para)
        
        # Branch subtitle with styling
        branch_para = Paragraph(
            f'<font color="{PDFColors.MEDIUM_GRAY}">{PDFBranding.BRANCH_NAME}</font>',
            self.styles['subtitle']
        )
        elements.append(branch_para)
        
        # Gold divider line
        elements.append(PDFLayoutHelpers.create_gold_border_line())
        elements.append(PDFLayoutHelpers.create_spacer(0.25))
    
    def _add_report_title(self, elements, title, subtitle=None):
        """Add report-specific title section"""
        # Main title
        title_para = Paragraph(title, self.styles['title'])
        elements.append(title_para)
        
        # Optional subtitle (date range, etc.)
        if subtitle:
            subtitle_para = Paragraph(subtitle, self.styles['subtitle'])
            elements.append(subtitle_para)
        
        elements.append(PDFLayoutHelpers.create_spacer(0.2))
    
    def _add_professional_footer(self, elements):
        """Add professional footer - Note: Footer is now drawn via canvas callback"""
        # Footer is handled by _footer_canvas callback, so we just add spacing
        elements.append(PDFLayoutHelpers.create_spacer(0.5))
    
    def _create_summary_box(self, summary_data):
        """Create styled summary metrics box"""
        data = [[label, value] for label, value in summary_data.items()]
        table = Table(data, colWidths=[3*inch, 2.5*inch])
        table.setStyle(PDFTableStyles.get_summary_table_style())
        return table
    
    def _create_data_table(self, data, col_widths=None):
        """Create professional data table"""
        table = Table(data, colWidths=col_widths)
        table.setStyle(PDFTableStyles.get_standard_table_style())
        return table
    
    # ================================================================
    # REPORT 1: Sales Performance Report
    # ================================================================
    def generate_sales_performance_report(self, report_data):
        """Generate Report 1: Sales Performance Report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter, 
            topMargin=0.5*inch,
            bottomMargin=0.8*inch,  # Increased for footer space
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
            )
        elements = []
        
        # Header
        self._add_professional_header(elements)
        
        # Date range
        start_date = report_data.get('date_range', {}).get('start', 'None')
        end_date = report_data.get('date_range', {}).get('end', 'None')
        date_range = f"{start_date} to {end_date}" if start_date != 'None' and end_date != 'None' else "None to None"
        
         # Report title
        self._add_report_title(elements, "Sales Performance Report", f"Report Period: {date_range}")
        
        # Summary section
        elements.append(Paragraph("Summary", self.styles['section']))
        
        summary = report_data.get('summary', {})
        summary_data = {
            'Total Revenue': f"${summary.get('total_income', 0):,.2f}",
            'Total Quantity Sold': f"{summary.get('total_quantity_sold', 0):,}",
            'Total Transactions': f"{summary.get('total_transactions', 0):,}"
        }
        
        summary_table = self._create_summary_box(summary_data)
        elements.append(summary_table)
        elements.append(PDFLayoutHelpers.create_spacer(0.3))
        
        # Sales details
        if report_data.get('sales'):
            elements.append(Paragraph("Sales Details", self.styles['section']))
            
            sales_data = [['Sale ID', 'Date', 'Product', 'Qty', 'Price', 'Retailer']]
            
            for sale in report_data['sales'][:50]:  # Limit to 50 for PDF
                sales_data.append([
                    str(sale.get('sale_id', 'N/A')),
                    sale.get('date', 'N/A')[:10],
                    sale.get('product_name', 'N/A')[:25],
                    str(sale.get('quantity_sold', 0)),
                    f"${sale.get('total_price', 0):,.2f}",
                    sale.get('retailer_name', 'N/A')[:20]
                ])
            
            sales_table = self._create_data_table(
                sales_data, 
                col_widths=[0.7*inch, 1*inch, 2*inch, 0.6*inch, 1*inch, 1.5*inch]
            )
            elements.append(sales_table)
        
        # Footer spacing (actual footer drawn via canvas)
        self._add_professional_footer(elements)
        
        # Build PDF with footer callback
        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer
    
    # ================================================================
    # REPORT 2: Category Distribution Report
    # ================================================================
    def generate_category_distribution_report(self, report_data):
        """Generate Report 2: Category Distribution Report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                topMargin=0.5*inch, bottomMargin=0.8*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        elements = []
        
        # Header
        self._add_professional_header(elements)
        self._add_report_title(elements, "Category Distribution Table")
        
        # Summary
        summary_text = {
            'Total Categories': str(report_data['summary']['total_categories']),
            'Total Stock': f"{report_data['summary']['total_stock']:,} units"
        }
        elements.append(Paragraph("Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))
        
        # Category table
        elements.append(Paragraph("Category Breakdown", self.styles['section']))
        cat_data = [['Category', 'Products', 'Stock Quantity', 'Share']]
        
        for cat in report_data['categories']:
            cat_data.append([
                cat['category_name'],
                str(cat['number_of_products']),
                f"{cat['total_stock_quantity']:,}",
                f"{cat['percentage_share']:.1f}%"
            ])
        
        cat_table = self._create_data_table(
            cat_data,
            col_widths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch]
        )
        elements.append(cat_table)
        
        # Footer spacing
        self._add_professional_footer(elements)
        
        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer
    
    # ================================================================
    # REPORT 3: Retailer Performance Report
    # ================================================================
    def generate_retailer_performance_report(self, report_data):
        """Generate Report 3: Retailer Performance Report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                topMargin=0.5*inch, bottomMargin=0.8*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        elements = []
        
        # Header
        self._add_professional_header(elements)
        
        # Report title
        self._add_report_title(elements, "Retailer Performance Report")
        
        # Summary
        summary_text = {
            'Total Retailers': str(report_data['summary']['total_retailers']),
            'Active Today': str(report_data['summary']['active_today'])
        }
        
        elements.append(Paragraph("Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))
        
        # Retailer table
        elements.append(Paragraph("Performance Metrics", self.styles['section']))
        ret_data = [['Retailer', 'Daily Quota', 'Today\'s Sales', 'Progress', 'Streak', 'Total Sales']]
        
        for ret in report_data['retailers']:
            ret_data.append([
                ret['retailer_name'][:25],
                f"${ret['daily_quota']:,.2f}",
                f"${ret['current_sales']:,.2f}",
                f"{ret['quota_progress']:.1f}%",
                str(ret['streak_count']),
                f"${ret['total_sales']:,.2f}"
            ])
        
        ret_table = self._create_data_table(
            ret_data,
            col_widths=[2*inch, 1*inch, 1*inch, 0.8*inch, 0.7*inch, 1*inch]
        )
        elements.append(ret_table)
        
        # Footer spacing
        self._add_professional_footer(elements)
        
        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer
    
    # ================================================================
    # REPORT 4: Low-Stock and Expiration Alert Report
    # ================================================================
    def generate_alerts_report(self, report_data):
        """Generate Report 4: Low-Stock and Expiration Alert Report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                topMargin=0.5*inch, bottomMargin=0.8*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        elements = []
        
        # Header
        self._add_professional_header(elements)
        
        # Report title
        self._add_report_title(elements, "Low-Stock & Expiration Alert Report")
        
        # Summary
        summary_text = {
            'Total Alerts': str(report_data['summary']['total_alerts']),
            'Critical': str(report_data['summary']['critical_alerts']), 
            'Warning': str(report_data['summary']['warning_alerts'])
        }
        elements.append(Paragraph("Alert Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))
        
        # Alerts table
        elements.append(Paragraph("Alert Details", self.styles['section']))
        alert_data = [['Product', 'Current Stock', 'Min Level', 'Expiration', 'Status', 'Severity']]
        
        for alert in report_data['alerts']:
            # Color code severity
            alert_data.append([
                alert['product_name'][:30],
                str(alert['current_stock']),
                str(alert['min_stock_level']),
                alert['expiration_date'] or 'N/A',
                alert['alert_status'],
                alert['severity']
            ])
        
        alert_table = self._create_data_table(
            alert_data,
            col_widths=[2*inch, 1*inch, 0.9*inch, 1*inch, 1.5*inch, 0.8*inch]
        )
        
        elements.append(alert_table)
        
        # Footer spacing
        self._add_professional_footer(elements)
        
        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer
    
    # ================================================================
    # REPORT 5: Managerial Activity Log Report
    # ================================================================
    def generate_managerial_activity_report(self, report_data):
        """Generate Report 5: Managerial Activity Log Report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                topMargin=0.5*inch, bottomMargin=0.8*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        elements = []
        
        # Header
        self._add_professional_header(elements)
        
        # Date range
        date_range = f"{report_data['date_range']['start']} to {report_data['date_range']['end']}"

        # Report title
        self._add_report_title(elements, "Managerial Activity Log Report", f"Report Period: {date_range}")
        
        # Summary
        summary_text = {
            'Total Actions': str(report_data['summary']['total_actions']),
            'Unique Managers': str(report_data['summary']['unique_managers'])
            }
        elements.append(Paragraph("Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))
        
        # Activity table
        elements.append(Paragraph("Activity Log", self.styles['section']))
        log_data = [['Log ID', 'Product', 'Action', 'Manager', 'Date/Time']]
        
        for log in report_data['logs'][:100]:  # Limit to 100
            log_data.append([
                str(log['log_id']),
                log['product_name'][:25],
                log['action_performed'],
                log['manager_name'][:20],
                log['date_time'][:16]
            ])
        
        log_table = self._create_data_table(
            log_data,
            col_widths=[0.7*inch, 2*inch, 1.3*inch, 1.5*inch, 1.5*inch]
        )
        elements.append(log_table)
        
        # Footer spacing
        self._add_professional_footer(elements)
        
        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer
    
    # ================================================================
    # REPORT 6: Detailed Sales Transaction Report
    # ================================================================
    def generate_transactions_report(self, report_data):
        """Generate Report 6: Detailed Sales Transaction Report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                topMargin=0.5*inch, bottomMargin=0.8*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        elements = []
        
        # Header
        self._add_professional_header(elements)

        # Report title
        self._add_report_title(elements, "Sales Performance Report")

        # Summary
        summary_text = {
            'Total Revenue': f"${report_data['summary']['total_revenue']:,.2f}",  # Corrected key from 'total_income' to 'total_revenue'
            'Total Transactions': f"{report_data['summary']['total_transactions']:,}",
            'Total Sales Count': f"{report_data['summary']['total_sales_count']:,}",
            'Total Items Sold': f"{report_data['summary']['total_items_sold']:,}"
        }
        elements.append(Paragraph("Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))

        # Date range (if available)
        start_date = report_data['date_range']['start']
        end_date = report_data['date_range']['end']
        date_range = f"{start_date} to {end_date}" if start_date and end_date else 'Not Specified'

        elements.append(Paragraph(f"Report Period: {date_range}", self.styles['section']))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))

        # Sales Breakdown table
        elements.append(Paragraph("Sales Breakdown", self.styles['section']))
        sales_data = [['Sale ID', 'Product', 'Brand', 'Quantity Sold', 'Unit Price', 'Line Total', 'Retailer']]

        # Add sales data to the table
        for transaction in report_data['transactions']:
            sales_data.append([
                str(transaction['sale_id']),
                transaction['product_name'],
                transaction['product_brand'],
                str(transaction['quantity_sold']),
                f"${transaction['unit_price']:.2f}",
                f"${transaction['line_total']:.2f}",
                transaction['retailer_name']
            ])
        
        # Create the sales table
        sales_table = self._create_data_table(
            sales_data,
            col_widths=[0.8*inch, 2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1.5*inch]
        )
        elements.append(sales_table)

        # Footer spacing
        self._add_professional_footer(elements)

        # Build the PDF document with footer callback
        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer
            
    
    # ================================================================
    # REPORT 7: User Accounts Report
    # ================================================================
    def generate_user_accounts_report(self, report_data):
        """Generate Report 7: User Accounts Report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                topMargin=0.5*inch, bottomMargin=0.8*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        elements = []
        
        # Header
        self._add_professional_header(elements)
        
        # Report title
        self._add_report_title(elements, "User Accounts Report")
        
        # Summary
        summary = report_data['summary']
        summary_text = {
            'Total Users': str(summary['total_users']),
            'Admins': str(summary['admins']),
            'Managers': str(summary['managers']),
            'Retailers': str(summary['retailers'])
            }
        elements.append(Paragraph("Summary", self.styles['section']))
        elements.append(self._create_summary_box(summary_text))
        elements.append(PDFLayoutHelpers.create_spacer(0.3))
        
        # User table
        elements.append(Paragraph("User Details", self.styles['section']))
        user_data = [['User ID', 'Username', 'Full Name', 'Role', 'Status']]
        
        for user in report_data['users']:
            user_data.append([
                str(user['user_id']),
                user['username'][:20],
                user['full_name'][:25],
                user['role'].capitalize(),
                user['account_status']
            ])
        
        user_table = self._create_data_table(
            user_data,
            col_widths=[0.8*inch, 1.5*inch, 2*inch, 1.2*inch, 1.2*inch]
        )
        elements.append(user_table)
        
        # Footer spacing
        self._add_professional_footer(elements)
        
        doc.build(elements, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
        buffer.seek(0)
        return buffer