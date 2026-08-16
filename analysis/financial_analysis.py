from collections import defaultdict
from typing import Any, Dict, List, Optional
import re


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _clean_number(value: Any) -> Optional[float]:
    """
    Convert financial values such as:
    10000
    "10,000"
    "$10,000"
    "₹10,000"
    "10,000.50"
    "(5000)"
    into float.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    # Handle negative values represented as (5000)
    negative = text.startswith("(") and text.endswith(")")

    # Remove currency symbols and commas
    text = text.replace(",", "")
    text = text.replace("$", "")
    text = text.replace("₹", "")
    text = text.replace("€", "")
    text = text.replace("£", "")

    # Remove percentage sign if present
    text = text.replace("%", "")

    # Keep only numbers, decimal point and minus sign
    text = re.sub(r"[^0-9.\-]", "", text)

    if not text:
        return None

    try:
        number = float(text)

        if negative:
            number = -abs(number)

        return number

    except ValueError:
        return None


def _get_value(row: Dict[str, Any], key: str) -> Optional[float]:
    """
    Safely extract and convert a numeric value from a row.
    """

    value = row.get(key)

    if value is None:
        return None

    return _clean_number(value)


def _get_rows(content: Any) -> List[Dict[str, Any]]:
    """
    Extract rows from different possible content formats.
    """

    if content is None:
        return []

    # List-shaped content. This can be either:
    #   (a) already a flat list of row dicts, e.g. [{"Revenue": ...}, ...]
    #   (b) a list of sheet-wrapper objects produced by the Excel
    #       extractor, e.g. [{"sheet_name": "Sheet1", "rows": 6,
    #       "columns": 7, "data": [{"Revenue": ...}, ...]}]
    # Case (b) must be unwrapped, or every sheet wrapper gets treated
    # as a single row with none of the expected fields (Revenue,
    # Category, Amount, etc.), which is why rows=1 was being reported
    # regardless of how many actual data rows the sheet contained.
    if isinstance(content, list):

        rows: List[Dict[str, Any]] = []

        for item in content:

            if not isinstance(item, dict):
                continue

            sheet_data = item.get("data")

            if isinstance(sheet_data, list):

                rows.extend(
                    row for row in sheet_data
                    if isinstance(row, dict)
                )

            else:
                # Not a sheet wrapper -- treat as a row itself
                rows.append(item)

        return rows

    # Dictionary containing rows
    if isinstance(content, dict):

        for key in ["rows", "data", "records"]:

            value = content.get(key)

            if isinstance(value, list):

                return [
                    row for row in value
                    if isinstance(row, dict)
                ]

        # Single dictionary row
        return [content]

    return []


def _get_classification(record: Dict[str, Any]) -> str:
    """
    Get document classification from a record.
    """

    classification = (
        record.get("classification")
        or record.get("document_type")
        or record.get("type")
        or ""
    )

    return str(classification).strip()


def _normalize_text(value: Any) -> str:
    """
    Normalize text for comparison.
    """

    if value is None:
        return ""

    text = str(value).strip().lower()

    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())


def _is_profit_loss(classification: str) -> bool:

    text = _normalize_text(classification)

    return (
        "profit loss" in text
        or "profit and loss" in text
        or "income statement" in text
        or text in {
            "p and l",
            "p l",
            "pl",
        }
    )


def _is_balance_sheet(classification: str) -> bool:

    text = _normalize_text(classification)

    return "balance sheet" in text


def _is_invoice_document(classification: str) -> bool:

    text = _normalize_text(classification)

    return (
        "invoice" in text
        or "invoices" in text
        or "accounts receivable" in text
    )


# ============================================================
# MAIN ANALYZER
# ============================================================

def analyze_financial_documents(
    extracted_records: List[Dict[str, Any]]
) -> Dict[str, Any]:

    metrics = {
        "total_revenue": None,
        "total_cogs": None,
        "total_operating_expenses": None,
        "total_gross_profit": None,
        "total_net_profit": None,
        "overall_profit_margin": None,
        "average_monthly_profit_margin": None,
        "current_ratio": None,
        "total_accounts_receivable": None,
        "total_accounts_payable": None,
        "total_overdue_invoice_amount": None,
        "total_pending_invoice_amount": None,
        "monthly_revenue_trend": [],
        "monthly_expense_trend": [],
        "monthly_net_profit_trend": [],
        "monthly_profit_margin_trend": [],
    }

    explanations: Dict[str, str] = {}
    flags: List[Dict[str, Any]] = []

    # ========================================================
    # STORAGE
    # ========================================================

    revenue_values = []
    cogs_values = []
    expense_values = []
    net_profit_values = []

    current_assets = []
    current_liabilities = []

    receivables = []
    payables = []

    monthly_revenue = defaultdict(float)
    monthly_expenses = defaultdict(float)
    monthly_net_profit = defaultdict(float)
    monthly_margin = {}

    overdue_amount = 0.0
    pending_amount = 0.0

    # ========================================================
    # MONTH NORMALIZATION
    # ========================================================

    month_map = {
        "jan": "Jan",
        "january": "Jan",
        "feb": "Feb",
        "february": "Feb",
        "mar": "Mar",
        "march": "Mar",
        "apr": "Apr",
        "april": "Apr",
        "may": "May",
        "jun": "Jun",
        "june": "Jun",
        "jul": "Jul",
        "july": "Jul",
        "aug": "Aug",
        "august": "Aug",
        "sep": "Sep",
        "september": "Sep",
        "oct": "Oct",
        "october": "Oct",
        "nov": "Nov",
        "november": "Nov",
        "dec": "Dec",
        "december": "Dec",
    }

    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    def normalize_month(value):

        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        # Month name
        if text.lower() in month_map:
            return month_map[text.lower()]

        # Numeric month
        try:
            number = int(float(text))

            if 1 <= number <= 12:
                return month_names[number - 1]

        except (ValueError, TypeError):
            pass

        return text

    # ========================================================
    # MONTH ORDER
    # ========================================================

    month_order = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }

    # ========================================================
    # PROCESS DOCUMENTS
    # ========================================================

    for record in extracted_records:

        if not isinstance(record, dict):
            continue

        # Ignore failed documents
        if record.get("status") == "error":
            continue

        content = record.get("content")

        if content is None:
            continue

        classification = _get_classification(record)
        rows = _get_rows(content)

        # ====================================================
        # PROFIT & LOSS
        # ====================================================

        if _is_profit_loss(classification):

            for row in rows:

                month = normalize_month(
                    row.get("Month")
                )

                revenue = _get_value(
                    row,
                    "Revenue"
                )

                cogs = _get_value(
                    row,
                    "Cost_of_Goods_Sold"
                )

                expenses = _get_value(
                    row,
                    "Operating_Expenses"
                )

                net_profit = _get_value(
                    row,
                    "Net_Profit"
                )

                # -------------------------------
                # TOTAL VALUES
                # -------------------------------

                if revenue is not None:
                    revenue_values.append(revenue)

                if cogs is not None:
                    cogs_values.append(cogs)

                if expenses is not None:
                    expense_values.append(expenses)

                if net_profit is not None:
                    net_profit_values.append(net_profit)

                # -------------------------------
                # MONTHLY TRENDS
                # -------------------------------

                if month:

                    if revenue is not None:
                        monthly_revenue[month] += revenue

                    if expenses is not None:
                        monthly_expenses[month] += expenses

                    if net_profit is not None:
                        monthly_net_profit[month] += net_profit

        # ====================================================
        # BALANCE SHEET
        # ====================================================

        elif _is_balance_sheet(classification):

            for row in rows:

                category = _normalize_text(
                    row.get("Category")
                )

                amount = _clean_number(
                    row.get("Amount")
                )

                if amount is None:
                    continue

                # Current assets
                if category == "current assets":

                    current_assets.append(amount)

                # Current liabilities
                elif category == "current liabilities":

                    current_liabilities.append(amount)

                # Accounts receivable
                elif "accounts receivable" in category:

                    receivables.append(amount)

                # Accounts payable
                elif "accounts payable" in category:

                    payables.append(amount)

        # ====================================================
        # INVOICES
        # ====================================================

        elif _is_invoice_document(classification):

            for row in rows:

                amount = _clean_number(
                    row.get("Amount")
                )

                if amount is None:
                    continue

                status = _normalize_text(
                    row.get("Payment_Status")
                )

                if status == "overdue":

                    overdue_amount += amount

                elif status == "pending":

                    pending_amount += amount

    # ========================================================
    # TOTAL REVENUE
    # ========================================================

    if revenue_values:

        metrics["total_revenue"] = sum(
            revenue_values
        )

    else:

        explanations["total_revenue"] = (
            "No revenue values were found in the uploaded "
            "Profit & Loss documents."
        )

    # ========================================================
    # TOTAL COGS
    # ========================================================

    if cogs_values:

        metrics["total_cogs"] = sum(
            cogs_values
        )

    else:

        explanations["total_cogs"] = (
            "No Cost of Goods Sold values were found."
        )

    # ========================================================
    # TOTAL OPERATING EXPENSES
    # ========================================================

    if expense_values:

        metrics["total_operating_expenses"] = sum(
            expense_values
        )

    else:

        explanations["total_operating_expenses"] = (
            "No operating expense values were found."
        )

    # ========================================================
    # GROSS PROFIT
    # ========================================================

    if (
        metrics["total_revenue"] is not None
        and metrics["total_cogs"] is not None
    ):

        metrics["total_gross_profit"] = (
            metrics["total_revenue"]
            - metrics["total_cogs"]
        )

    else:

        explanations["total_gross_profit"] = (
            "Gross profit could not be calculated because "
            "revenue or COGS data is missing."
        )

    # ========================================================
    # NET PROFIT
    # ========================================================

    if net_profit_values:

        metrics["total_net_profit"] = sum(
            net_profit_values
        )

    elif (
        metrics["total_revenue"] is not None
        and metrics["total_cogs"] is not None
        and metrics["total_operating_expenses"] is not None
    ):

        metrics["total_net_profit"] = (
            metrics["total_revenue"]
            - metrics["total_cogs"]
            - metrics["total_operating_expenses"]
        )

    else:

        explanations["total_net_profit"] = (
            "Net profit could not be calculated because "
            "required financial values are missing."
        )

    # ========================================================
    # OVERALL PROFIT MARGIN
    # ========================================================

    if (
        metrics["total_revenue"] is not None
        and metrics["total_net_profit"] is not None
        and metrics["total_revenue"] != 0
    ):

        metrics["overall_profit_margin"] = (
            metrics["total_net_profit"]
            / metrics["total_revenue"]
        ) * 100

    # ========================================================
    # MONTHLY PROFIT MARGINS
    # ========================================================

    all_months = set()

    all_months.update(monthly_revenue.keys())
    all_months.update(monthly_expenses.keys())
    all_months.update(monthly_net_profit.keys())

    for month in all_months:

        revenue = monthly_revenue.get(
            month,
            0
        )

        net_profit = monthly_net_profit.get(
            month,
            0
        )

        if revenue != 0:

            monthly_margin[month] = (
                net_profit / revenue
            ) * 100

    # ========================================================
    # AVERAGE MONTHLY PROFIT MARGIN
    # ========================================================

    if monthly_margin:

        metrics["average_monthly_profit_margin"] = (
            sum(monthly_margin.values())
            / len(monthly_margin)
        )

    # ========================================================
    # CURRENT RATIO
    # ========================================================

    if current_assets and current_liabilities:

        total_current_assets = sum(
            current_assets
        )

        total_current_liabilities = sum(
            current_liabilities
        )

        if total_current_liabilities != 0:

            metrics["current_ratio"] = (
                total_current_assets
                / total_current_liabilities
            )

    # ========================================================
    # ACCOUNTS RECEIVABLE
    # ========================================================

    if receivables:

        metrics["total_accounts_receivable"] = sum(
            receivables
        )

    # ========================================================
    # ACCOUNTS PAYABLE
    # ========================================================

    if payables:

        metrics["total_accounts_payable"] = sum(
            payables
        )

    # ========================================================
    # OVERDUE INVOICES
    # ========================================================

    if overdue_amount > 0:

        metrics["total_overdue_invoice_amount"] = (
            overdue_amount
        )

    # ========================================================
    # PENDING INVOICES
    # ========================================================

    if pending_amount > 0:

        metrics["total_pending_invoice_amount"] = (
            pending_amount
        )

    # ========================================================
    # SORT MONTHS
    # ========================================================

    sorted_months = sorted(
        all_months,
        key=lambda x: month_order.get(x, 99)
    )

    # ========================================================
    # MONTHLY REVENUE TREND
    # ========================================================

    metrics["monthly_revenue_trend"] = [

        {
            "month": month,
            "value": round(
                monthly_revenue.get(month, 0),
                2
            )
        }

        for month in sorted_months

        if month in monthly_revenue
    ]

    # ========================================================
    # MONTHLY EXPENSE TREND
    # ========================================================

    metrics["monthly_expense_trend"] = [

        {
            "month": month,
            "value": round(
                monthly_expenses.get(month, 0),
                2
            )
        }

        for month in sorted_months

        if month in monthly_expenses
    ]

    # ========================================================
    # MONTHLY NET PROFIT TREND
    # ========================================================

    metrics["monthly_net_profit_trend"] = [

        {
            "month": month,
            "value": round(
                monthly_net_profit.get(month, 0),
                2
            )
        }

        for month in sorted_months

        if month in monthly_net_profit
    ]

    # ========================================================
    # MONTHLY PROFIT MARGIN TREND
    # ========================================================

    metrics["monthly_profit_margin_trend"] = [

        {
            "month": month,
            "value": round(
                monthly_margin[month],
                2
            )
        }

        for month in sorted_months

        if month in monthly_margin
    ]

    # ========================================================
    # RISK FLAGS
    # ========================================================

    # --------------------------------------------------------
    # 1. LOW PROFIT MARGIN
    # --------------------------------------------------------

    if (
        metrics["overall_profit_margin"] is not None
        and metrics["overall_profit_margin"] < 12
    ):

        flags.append({
            "type": "low profit margin",
            "severity": "medium",
            "message": (
                "Overall profit margin is below 12%, "
                "indicating reduced profitability."
            )
        })

    # --------------------------------------------------------
    # 2. DECLINING PROFIT MARGIN
    # --------------------------------------------------------

    if len(monthly_margin) >= 2:

        ordered_margins = [
            monthly_margin[m]
            for m in sorted_months
            if m in monthly_margin
        ]

        if (
            len(ordered_margins) >= 2
            and ordered_margins[-1]
            < ordered_margins[0]
        ):

            flags.append({
                "type": "declining profit margin trend",
                "severity": "medium",
                "message": (
                    "Monthly profit margin has declined "
                    "over the available reporting period."
                )
            })

    # --------------------------------------------------------
    # 3. HIGH OVERDUE INVOICES
    # --------------------------------------------------------

    if (
        metrics["total_overdue_invoice_amount"] is not None
        and metrics["total_revenue"] is not None
        and metrics["total_revenue"] > 0
    ):

        overdue_ratio = (
            metrics["total_overdue_invoice_amount"]
            / metrics["total_revenue"]
        )

        if overdue_ratio >= 0.15:

            flags.append({
                "type": "high overdue receivables",
                "severity": "high",
                "message": (
                    "Overdue invoices represent at least "
                    "15% of revenue and may create "
                    "cash-flow pressure."
                )
            })

    # --------------------------------------------------------
    # 4. HIGH RECEIVABLES
    # --------------------------------------------------------

    if (
        metrics["total_accounts_receivable"] is not None
        and metrics["total_revenue"] is not None
        and metrics["total_revenue"] > 0
    ):

        receivable_ratio = (
            metrics["total_accounts_receivable"]
            / metrics["total_revenue"]
        )

        if receivable_ratio > 0.50:

            flags.append({
                "type": "high receivables compared with revenue",
                "severity": "medium",
                "message": (
                    "Accounts receivable are high compared "
                    "with revenue and may indicate slower "
                    "customer collections."
                )
            })

    # --------------------------------------------------------
    # 5. LOW CURRENT RATIO
    # --------------------------------------------------------

    if (
        metrics["current_ratio"] is not None
        and metrics["current_ratio"] < 1
    ):

        flags.append({
            "type": "low current ratio",
            "severity": "high",
            "message": (
                "Current liabilities exceed current assets, "
                "which may indicate short-term liquidity stress."
            )
        })

    # --------------------------------------------------------
    # 6. HIGH OPERATING EXPENSES
    # --------------------------------------------------------

    if (
        metrics["total_operating_expenses"] is not None
        and metrics["total_revenue"] is not None
        and metrics["total_revenue"] > 0
    ):

        expense_ratio = (
            metrics["total_operating_expenses"]
            / metrics["total_revenue"]
        )

        if expense_ratio > 0.70:

            flags.append({
                "type": "high operating expenses",
                "severity": "medium",
                "message": (
                    "Operating expenses consume more than "
                    "70% of revenue."
                )
            })

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "metrics": metrics,
        "flags": flags,
        "explanations": explanations,
    }