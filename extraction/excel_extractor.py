from io import BytesIO
from typing import Dict, List, Any

import pandas as pd


def extract_excel_data(file_bytes: bytes) -> List[Dict[str, Any]]:
    """Read Excel workbooks and return sheet-level table data."""
    if not file_bytes:
        raise ValueError("Excel file is empty.")

    workbook = pd.ExcelFile(BytesIO(file_bytes))
    extracted_sheets: List[Dict[str, Any]] = []

    for sheet_name in workbook.sheet_names:
        df = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)
        extracted_sheets.append({
            "sheet_name": sheet_name,
            "rows": df.shape[0],
            "columns": df.shape[1],
            "data": df.fillna("").to_dict(orient="records"),
        })

    return extracted_sheets
