from io import StringIO
from typing import Dict, Any

import pandas as pd


def extract_csv_data(file_bytes: bytes) -> Dict[str, Any]:
    """Read CSV files and return table data with metadata."""
    if not file_bytes:
        raise ValueError("CSV file is empty.")

    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("utf-8-sig", errors="replace")

    df = pd.read_csv(StringIO(text))

    return {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "data": df.fillna("").to_dict(orient="records"),
    }
