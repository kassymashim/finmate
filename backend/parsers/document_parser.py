"""
Document parser for financial documents.
Handles: CSV transaction files, PDF bank statements, receipt images.
"""

import pandas as pd
import os
from io import BytesIO
from pypdf import PdfReader


def parse_csv_transactions(file_path_or_buffer) -> pd.DataFrame:
    """Parse a CSV file containing transaction data."""
    df = pd.read_csv(file_path_or_buffer)

    expected_cols = {"date", "merchant", "amount"}
    actual_cols = set(df.columns.str.lower())

    if not expected_cols.issubset(actual_cols):
        df.columns = df.columns.str.lower().str.strip()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date", ascending=False)

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    return df


def parse_pdf_statement(file_path_or_buffer) -> str:
    """Extract text from a PDF bank statement."""
    if isinstance(file_path_or_buffer, (str, os.PathLike)):
        reader = PdfReader(file_path_or_buffer)
    else:
        reader = PdfReader(BytesIO(file_path_or_buffer.read()))

    text_content = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_content.append(text)

    return "\n\n".join(text_content)


def extract_transactions_from_text(text: str) -> list[dict]:
    """
    Attempt to extract structured transaction data from raw text.
    This is a basic pattern matcher - the LLM will handle complex cases.
    """
    import re

    transactions = []
    date_pattern = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    amount_pattern = r"[\$]?([\d,]+\.\d{2})"

    lines = text.split("\n")
    for line in lines:
        dates = re.findall(date_pattern, line)
        amounts = re.findall(amount_pattern, line)

        if dates and amounts:
            description = re.sub(date_pattern, "", line)
            description = re.sub(r"[\$]?[\d,]+\.\d{2}", "", description).strip()
            description = re.sub(r"[^\w\s]", "", description).strip()

            if description and len(description) > 2:
                transactions.append({
                    "date": dates[0],
                    "description": description,
                    "amount": float(amounts[0].replace(",", "")),
                })

    return transactions


def get_spending_summary(df: pd.DataFrame) -> dict:
    """Generate a spending summary from transaction DataFrame."""
    if df.empty:
        return {"error": "No transactions found"}

    expenses = df[df["amount"] < 0].copy()
    income = df[df["amount"] > 0].copy()

    summary = {
        "total_income": float(income["amount"].sum()),
        "total_expenses": float(expenses["amount"].sum()),
        "net_cashflow": float(df["amount"].sum()),
        "transaction_count": len(df),
        "date_range": {
            "start": str(df["date"].min()),
            "end": str(df["date"].max()),
        },
    }

    if "category" in df.columns:
        category_spending = (
            expenses.groupby("category")["amount"]
            .agg(["sum", "count", "mean"])
            .round(2)
            .to_dict("index")
        )
        summary["by_category"] = category_spending

    if "merchant" in df.columns:
        top_merchants = (
            expenses.groupby("merchant")["amount"]
            .sum()
            .sort_values()
            .head(10)
            .to_dict()
        )
        summary["top_merchants"] = top_merchants

    return summary
