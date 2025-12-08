# desktop_app/services/report_generator.py
"""
Desktop side report service for StockaDoodle.

- Calls backend /api/v1/reports/* JSON endpoints
- Downloads PDFs reliably via raw=True or download_pdf_report()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from desktop_app.utils.api_wrapper import get_api


@dataclass(frozen=True)
class ReportSpec:
    key: str
    label: str
    endpoint: str
    needs_date_range: bool = False
    needs_days_ahead: bool = False
    pdf_endpoint: Optional[str] = None
    pdf_type_param: Optional[str] = None  # for download_pdf_report helper


REPORT_SPECS: Dict[str, ReportSpec] = {
    "sales_performance": ReportSpec(
        key="sales_performance",
        label="Sales Performance",
        endpoint="/reports/sales-performance",
        pdf_endpoint="/reports/sales-performance/pdf",
        pdf_type_param="sales-performance",
        needs_date_range=True,
    ),
    "category_distribution": ReportSpec(
        key="category_distribution",
        label="Category Distribution",
        endpoint="/reports/category-distribution",
        pdf_endpoint="/reports/category-distribution/pdf",
        pdf_type_param="category-distribution",
    ),
    "retailer_performance": ReportSpec(
        key="retailer_performance",
        label="Retailer Performance",
        endpoint="/reports/retailer-performance",
        pdf_endpoint="/reports/retailer-performance/pdf",
        pdf_type_param="retailer-performance",
    ),
    "alerts": ReportSpec(
        key="alerts",
        label="Low-Stock & Expiration Alerts",
        endpoint="/reports/alerts",
        pdf_endpoint="/reports/alerts/pdf",
        pdf_type_param="alerts",
        needs_days_ahead=True,
    ),
    "managerial_activity": ReportSpec(
        key="managerial_activity",
        label="Managerial Activity Log",
        endpoint="/reports/managerial-activity",
        pdf_endpoint="/reports/managerial-activity/pdf",
        pdf_type_param="managerial-activity",
        needs_date_range=True,
    ),
    "transactions": ReportSpec(
        key="transactions",
        label="Detailed Sales Transactions",
        endpoint="/reports/transactions",
        pdf_endpoint="/reports/transactions/pdf",
        pdf_type_param="transactions",
        needs_date_range=True,
    ),
    "user_accounts": ReportSpec(
        key="user_accounts",
        label="User Accounts",
        endpoint="/reports/user-accounts",
        pdf_endpoint="/reports/user-accounts/pdf",
        pdf_type_param="user-accounts",
    ),
}


class DesktopReportGenerator:
    """
    Service consumed by ReportsPage.

    Public API:
      - list_reports() -> List[ReportSpec]
      - generate_report(key, ...) -> dict
      - download_pdf(key, ...) -> bytes
    """

    @staticmethod
    def list_reports() -> List[ReportSpec]:
        return list(REPORT_SPECS.values())

    @staticmethod
    def get_spec(key: str) -> ReportSpec:
        if key not in REPORT_SPECS:
            raise ValueError(f"Unknown report key: {key}")
        return REPORT_SPECS[key]

    @staticmethod
    def generate_report(
        key: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days_ahead: Optional[int] = None,
    ) -> Dict[str, Any]:
        spec = DesktopReportGenerator.get_spec(key)
        params: Dict[str, Any] = {}

        if spec.needs_date_range:
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

        if spec.needs_days_ahead:
            if days_ahead is not None:
                params["days_ahead"] = int(days_ahead)

        api = get_api()
        result = api._request("GET", spec.endpoint, params=params or None)
        if isinstance(result, dict):
            return result
        raise RuntimeError("Expected JSON dict but got non-JSON response.")

    @staticmethod
    def download_pdf(
        key: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days_ahead: Optional[int] = None,
    ) -> bytes:
        spec = DesktopReportGenerator.get_spec(key)
        if not spec.pdf_endpoint:
            raise ValueError(f"Report '{spec.label}' does not define a PDF endpoint.")

        params: Dict[str, Any] = {}

        if spec.needs_date_range:
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

        if spec.needs_days_ahead:
            if days_ahead is not None:
                params["days_ahead"] = int(days_ahead)

        api = get_api()

        # Prefer generic raw download through _request
        try:
            raw = api._request("GET", spec.pdf_endpoint, params=params or None, raw=True)
            if isinstance(raw, (bytes, bytearray)):
                return bytes(raw)
        except Exception:
            pass

        # Fallback to explicit helper if present
        if hasattr(api, "download_pdf_report") and spec.pdf_type_param:
            return api.download_pdf_report(spec.pdf_type_param, **params)

        raise RuntimeError("Unable to download PDF - no compatible method found.")
