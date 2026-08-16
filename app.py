import os
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from extraction.pdf_extractor import extract_pdf_text
from extraction.excel_extractor import extract_excel_data
from extraction.csv_extractor import extract_csv_data
from agents.document_agent import classify_document
from analysis.financial_analysis import analyze_financial_documents

load_dotenv()

SUPPORTED_EXTENSIONS = {
    ".pdf": "PDF",
    ".xlsx": "Excel",
    ".xls": "Excel",
    ".csv": "CSV",
}


def detect_document_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(suffix, "Unknown")


def count_actual_rows(content: Any) -> Any:
    """
    Count the real number of data rows in extracted content, not just
    the number of top-level sheet wrappers. Content is typically shaped
    like [{"sheet_name": ..., "data": [...]}], so len(content) alone
    always returns the sheet count (usually 1), which is what produced
    the misleading 'rows=1' debug output regardless of how many actual
    rows were in the sheet.
    """
    if not isinstance(content, list):
        return "N/A"

    total = 0
    counted_anything = False

    for item in content:
        if isinstance(item, dict) and isinstance(item.get("data"), list):
            total += len(item["data"])
            counted_anything = True
        elif isinstance(item, dict):
            # flat row, not a sheet wrapper
            total += 1
            counted_anything = True

    return total if counted_anything else "N/A"


def extract_file(file: Any) -> Dict[str, Any]:
    """Extract content from a single uploaded file."""
    file_name = file.name
    file_type = detect_document_type(file_name)
    file_bytes = file.getvalue()

    result: Dict[str, Any] = {
        "name": file_name,
        "type": file_type,
        "content": None,
        "status": "ok",
        "error": None,
    }

    try:
        if file_type == "PDF":
            result["content"] = extract_pdf_text(file_bytes)
        elif file_type == "Excel":
            result["content"] = extract_excel_data(file_bytes)
        elif file_type == "CSV":
            result["content"] = extract_csv_data(file_bytes)
        else:
            result["status"] = "unsupported"
            result["error"] = "Unsupported file type."
    except Exception as exc:  # pragma: no cover - UI-level error handling
        result["status"] = "error"
        result["error"] = str(exc)

    return result


st.set_page_config(page_title="Financial Document Intelligence Agent", layout="wide")
st.title("Financial Document Intelligence Agent for SMEs")

st.write(
    "Upload one or more financial documents. The system will analyze them automatically once uploaded."
)

uploaded_files = st.file_uploader(
    "Upload financial documents",
    type=["pdf", "xlsx", "xls", "csv"],
    accept_multiple_files=True,
)

if uploaded_files:
    extracted_records: List[Dict[str, Any]] = []

    for uploaded_file in uploaded_files:
        extracted = extract_file(uploaded_file)

        if extracted["status"] == "ok":
            # Classify once per file and reuse everywhere below, instead
            # of calling classify_document() again for the file table and
            # again for the extraction display. Avoids redundant work and
            # any risk of inconsistent results if classification isn't
            # perfectly deterministic.
            extracted["classification"] = classify_document(
                extracted["name"],
                extracted["content"],
                extracted["type"],
            )

        extracted_records.append(extracted)

        classification_label = (
            extracted.get("classification", {}).get("classification", "N/A")
            if extracted.get("classification")
            else "N/A"
        )

        st.write(
            f"DEBUG: {extracted['name']} | type={extracted['type']} | "
            f"classification={classification_label} | "
            f"rows={count_actual_rows(extracted.get('content'))}"
        )

    st.subheader("Uploaded Files")
    uploaded_df = pd.DataFrame(
        [
            {
                "File Name": item["name"],
                "Document Type": item["type"],
                "Status": item["status"],
                "Classification": (
                    item["classification"]["classification"]
                    if item["status"] == "ok" and item.get("classification")
                    else "Unavailable"
                ),
                "Error": item["error"] or "",
            }
            for item in extracted_records
        ]
    )
    st.dataframe(uploaded_df, use_container_width=True)

    st.subheader("Extraction Output")
    for item in extracted_records:
        st.markdown(f"### {item['name']} ({item['type']})")
        if item["status"] == "ok":
            classification = item["classification"]
            st.caption(
                f"Classification: {classification['classification']} "
                f"(confidence: {classification['confidence']})"
            )
            st.json(item["content"])
        else:
            st.warning(item["error"])

    st.subheader("📊 Current Financial State")
    financial_result = analyze_financial_documents(extracted_records)

    # TEMPORARY DEBUG MARKER — confirms which analyzer code is actually
    # executing. Remove this line once you've verified the fix is live.
    st.write(
        f"### 🔍 DEBUG MARKER: "
        f"{financial_result.get('debug_marker', 'NOT FOUND — OLD CODE RUNNING')}"
    )

    metrics = financial_result["metrics"]
    flags = financial_result["flags"]

    metric_columns = st.columns(4)
    metric_values = [
        ("Total Revenue", metrics.get("total_revenue")),
        ("Total Net Profit", metrics.get("total_net_profit")),
        ("Overall Profit Margin", metrics.get("overall_profit_margin")),
        ("Current Ratio", metrics.get("current_ratio")),
    ]

    for idx, (label, value) in enumerate(metric_values):
        with metric_columns[idx % 4]:
            if value is None:
                st.metric(label, "Unavailable")
            elif label.endswith("Margin"):
                st.metric(label, f"{value:.2f}%")
            else:
                st.metric(label, f"{value:,.2f}")

    st.subheader("Financial Metrics")
    metric_df = pd.DataFrame(
        [
            {"Metric": key.replace("_", " ").title(), "Value": value}
            for key, value in metrics.items()
            if key not in [
                "monthly_revenue_trend",
                "monthly_expense_trend",
                "monthly_net_profit_trend",
                "monthly_profit_margin_trend",
            ]
        ]
    )
    st.dataframe(metric_df, use_container_width=True)

    st.subheader("Risk Flags")
    if flags:
        for flag in flags:
            st.warning(f"{flag['type']}: {flag['message']}")
    else:
        st.info("No deterministic risk flags were triggered from the available information.")

    st.subheader("Trend Analysis")
    trend_tab_data = {
        "Monthly Revenue Trend": metrics.get("monthly_revenue_trend", []),
        "Monthly Expense Trend": metrics.get("monthly_expense_trend", []),
        "Monthly Net Profit Trend": metrics.get("monthly_net_profit_trend", []),
        "Monthly Profit Margin Trend": metrics.get("monthly_profit_margin_trend", []),
    }

    for trend_name, trend_values in trend_tab_data.items():
        if trend_values:
            df = pd.DataFrame(trend_values)
            st.line_chart(df.set_index("month")["value"], use_container_width=True)
        else:
            st.caption(f"{trend_name}: No monthly data available.")

    st.subheader("Auto Analysis Trigger")
    st.success(
        "Documents uploaded, extracted, classified, and analyzed automatically "
        "with deterministic financial metrics and risk flags."
    )
else:
    st.info("No files uploaded yet. Please upload a PDF, Excel, or CSV file.")