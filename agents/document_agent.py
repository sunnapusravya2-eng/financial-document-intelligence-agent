import re
from typing import Any, Dict, List, Union


P_AND_L_KEYWORDS = [
    "profit and loss",
    "income statement",
    "p&l",
    "pl",
    "revenue",
    "expenses",
    "gross profit",
    "net profit",
    "operating income",
    "ebitda",
]

BALANCE_SHEET_KEYWORDS = [
    "balance sheet",
    "assets",
    "liabilities",
    "equity",
    "current assets",
    "current liabilities",
    "cash",
    "receivables",
    "payables",
]

CASH_FLOW_KEYWORDS = [
    "cash flow",
    "operating cash flow",
    "investing cash flow",
    "financing cash flow",
    "net cash",
    "cash from operations",
]

INVOICE_KEYWORDS = [
    "invoice",
    "invoiced",
    "transaction",
    "amount",
    "quantity",
    "unit price",
    "customer",
    "vendor",
    "date",
    "payment",
]


def _flatten_text(value: Any) -> str:
    """Convert extracted document structures into text for keyword matching."""
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        text_parts: List[str] = []
        for item in value:
            if isinstance(item, dict):
                text_parts.extend(_flatten_text(v) for v in item.values())
            else:
                text_parts.append(str(item))
        return " ".join(part for part in text_parts if part)

    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values())

    return str(value)


def _score_keywords(text: str, keywords: List[str]) -> int:
    normalized = re.sub(r"[^a-z0-9&\s]", " ", text.lower())
    score = 0
    for keyword in keywords:
        if keyword in normalized:
            score += 1
    return score


def classify_document(file_name: str, extracted_content: Any, file_type: str) -> Dict[str, Any]:
    """Classify the document based on filename and extracted content."""
    text = _flatten_text(extracted_content)
    name_text = file_name.lower()

    scores = {
        "Profit & Loss": _score_keywords(name_text + " " + text, P_AND_L_KEYWORDS),
        "Balance Sheet": _score_keywords(name_text + " " + text, BALANCE_SHEET_KEYWORDS),
        "Cash Flow": _score_keywords(name_text + " " + text, CASH_FLOW_KEYWORDS),
        "Invoice/Transactions": _score_keywords(name_text + " " + text, INVOICE_KEYWORDS),
    }

    if "profit" in name_text or "pnl" in name_text or "income statement" in name_text:
        scores["Profit & Loss"] += 3
    if "balance" in name_text and "sheet" in name_text:
        scores["Balance Sheet"] += 3
    if "cash" in name_text and "flow" in name_text:
        scores["Cash Flow"] += 3
    if "invoice" in name_text or "transaction" in name_text:
        scores["Invoice/Transactions"] += 3

    best_label, best_score = max(scores.items(), key=lambda item: item[1])

    if best_score == 0:
        return {
            "classification": "Unknown",
            "confidence": 0,
            "reasons": ["No strong financial-document keywords were found in the file name or extracted data."],
            "file_type": file_type,
        }

    return {
        "classification": best_label,
        "confidence": min(best_score, 5),
        "reasons": [
            f"Matched financial keywords associated with {best_label.lower()}.",
            f"Detected from file type: {file_type}.",
        ],
        "file_type": file_type,
    }
