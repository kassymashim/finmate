"""
FastAPI server for FinMate - serves the Next.js frontend.
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import json
import os

from backend.agents.finance_graph import run_finance_agent
from backend.parsers.document_parser import get_spending_summary
from backend.parsers.receipt_analyzer import analyze_receipt_image
from backend.mcp_server.finance_tools import categorize_transaction
from backend.utils.config import OPENAI_API_KEY
from backend.utils.guardrails import validate_input, validate_output
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(title="FinMate API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_transactions")

CANONICAL_CATEGORIES = {
    "groceries", "restaurants", "transportation", "housing", "utilities",
    "entertainment", "shopping", "healthcare", "subscriptions", "income", "other",
}

CATEGORY_ALIASES = {
    "clothing": "Shopping",
    "apparel": "Shopping",
    "retail": "Shopping",
    "fashion": "Shopping",
    "food": "Restaurants",
    "dining": "Restaurants",
    "grocery": "Groceries",
    "gas": "Transportation",
    "transport": "Transportation",
}


def _parse_amount(value) -> float:
    """Coerce OCR amounts (may be str, dict, or nested) to float."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("total", "amount", "value", "price"):
            if key in value:
                parsed = _parse_amount(value[key])
                if parsed > 0:
                    return parsed
        return 0.0
    try:
        cleaned = str(value).replace(",", "").replace("$", "").strip()
        return float(cleaned) if cleaned else 0.0
    except (TypeError, ValueError):
        return 0.0


def _extract_receipt_total(result: dict) -> float:
    """Pull total from common OCR field names and line items."""
    for key in ("total", "grand_total", "amount_due", "approved_amount"):
        parsed = _parse_amount(result.get(key))
        if parsed > 0:
            return parsed
    subtotal = _parse_amount(result.get("subtotal"))
    tax = _parse_amount(result.get("tax"))
    if subtotal > 0:
        return subtotal + tax if tax > 0 else subtotal
    items = result.get("items") or []
    if items:
        items_sum = sum(_parse_amount(i.get("amount")) for i in items if isinstance(i, dict))
        if items_sum > 0:
            return items_sum + tax if tax > 0 else items_sum
    return 0.0


def _resolve_category(merchant: str, gpt_suggestion: str | None) -> str:
    """Match quick-add: keyword rules first, then normalized GPT label."""
    category = categorize_transaction(merchant)
    if category != "Other":
        return category
    if not gpt_suggestion:
        return "Other"
    raw = str(gpt_suggestion).strip().lower()
    if raw in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[raw]
    normalized = str(gpt_suggestion).strip().title()
    if normalized.lower() in CANONICAL_CATEGORIES:
        return normalized
    return "Other"


def load_transactions():
    csv_path = os.path.join(DATA_PATH, "transactions.csv")
    if not os.path.exists(csv_path):
        from backend.utils.generate_synthetic_data import save_data
        save_data()
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_profile():
    profile_path = os.path.join(DATA_PATH, "user_profile.json")
    with open(profile_path) as f:
        return json.load(f)


class ChatMessage(BaseModel):
    message: str
    history: list[dict] = []


class QuickExpense(BaseModel):
    merchant: str
    amount: float


@app.get("/api/dashboard")
def get_dashboard():
    """Get full dashboard data: metrics, transactions, category breakdown."""
    df = load_transactions()
    profile = load_profile()

    expenses = df[df["amount"] < 0].copy()
    income = df[df["amount"] > 0].copy()

    total_income = float(income["amount"].sum())
    total_expenses = float(expenses["amount"].abs().sum())
    savings = total_income - total_expenses
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0
    num_months = max(expenses["date"].dt.to_period("M").nunique(), 1)

    # Category breakdown
    category_totals = (
        expenses.groupby("category")["amount"]
        .sum()
        .abs()
        .sort_values(ascending=False)
        .reset_index()
    )
    categories = [
        {"name": row["category"], "amount": round(row["amount"], 2)}
        for _, row in category_totals.iterrows()
    ]

    # Monthly trends
    expenses["month"] = expenses["date"].dt.strftime("%Y-%m")
    monthly = expenses.groupby(["month", "category"])["amount"].sum().abs().reset_index()
    months_list = sorted(monthly["month"].unique())
    monthly_data = []
    for month in months_list:
        month_entries = monthly[monthly["month"] == month]
        entry = {"month": month}
        for _, row in month_entries.iterrows():
            entry[row["category"]] = round(row["amount"], 2)
        monthly_data.append(entry)

    # Daily spending (last 60 days)
    recent_expenses = expenses[expenses["date"] >= expenses["date"].max() - pd.Timedelta(days=60)]
    daily = recent_expenses.groupby(recent_expenses["date"].dt.strftime("%Y-%m-%d"))["amount"].sum().abs()
    daily_data = [{"date": d, "amount": round(v, 2)} for d, v in daily.items()]

    # Recent transactions
    recent_txns = (
        expenses.nlargest(15, "date")[["date", "merchant", "category", "amount"]]
        .copy()
    )
    recent_txns["date"] = recent_txns["date"].dt.strftime("%Y-%m-%d")
    recent_txns["amount"] = recent_txns["amount"].round(2)
    transactions = recent_txns.to_dict("records")

    # All transactions (for month filtering on frontend)
    all_txns = expenses[["date", "merchant", "category", "amount"]].copy()
    all_txns["date"] = all_txns["date"].dt.strftime("%Y-%m-%d")
    all_txns["amount"] = all_txns["amount"].round(2)
    all_transactions = all_txns.to_dict("records")

    # Available months (sorted descending - most recent first)
    available_months = sorted(expenses["date"].dt.strftime("%Y-%m").unique(), reverse=True)

    return {
        "metrics": {
            "totalIncome": round(total_income, 2),
            "totalExpenses": round(total_expenses, 2),
            "netSavings": round(savings, 2),
            "savingsRate": round(savings_rate, 1),
            "avgMonthly": round(total_expenses / num_months, 2),
            "transactionCount": len(expenses),
        },
        "categories": categories,
        "monthlyTrends": monthly_data,
        "dailySpending": daily_data,
        "recentTransactions": transactions,
        "allTransactions": all_transactions,
        "availableMonths": available_months,
        "profile": profile,
    }


@app.post("/api/chat")
def chat(msg: ChatMessage):
    """Process a chat message through the finance agent with guardrails."""
    # Input guardrails: PII masking + prompt injection detection
    is_safe, cleaned_message, warning = validate_input(msg.message)

    if not is_safe:
        return {"response": warning, "intent": "blocked", "guardrail": "injection_detected"}

    df = load_transactions()
    profile = load_profile()
    summary = json.dumps(get_spending_summary(df), indent=2, default=str)

    chat_history = []
    for h in msg.history:
        if h["role"] == "user":
            chat_history.append(HumanMessage(content=h["content"]))
        else:
            chat_history.append(AIMessage(content=h["content"]))

    result = run_finance_agent(
        user_message=cleaned_message,
        transaction_data=summary,
        user_profile=json.dumps(profile),
        chat_history=chat_history,
    )

    # Output guardrails: mask any PII in response + add disclaimers
    safe_response = validate_output(result["response"])

    response_data = {
        "response": safe_response,
        "intent": result["intent"],
    }
    if warning:
        response_data["response"] = f"⚠️ {warning}\n\n{safe_response}"
        response_data["guardrail"] = "pii_masked"

    return response_data


@app.post("/api/expense")
def add_expense(expense: QuickExpense):
    """Add a quick expense, persist it to CSV, and return its category."""
    category = categorize_transaction(expense.merchant)
    date_str = pd.Timestamp.now().strftime("%Y-%m-%d")

    new_row = {
        "date": date_str,
        "merchant": expense.merchant,
        "category": category,
        "amount": -abs(expense.amount),
        "type": "debit",
        "description": f"Payment to {expense.merchant}",
    }

    csv_path = os.path.join(DATA_PATH, "transactions.csv")
    new_df = pd.DataFrame([new_row])
    new_df.to_csv(csv_path, mode="a", header=False, index=False)

    return {
        "merchant": expense.merchant,
        "amount": expense.amount,
        "category": category,
        "date": date_str,
    }


@app.get("/api/health")
def health():
    """Lightweight check that the API includes receipt-save support."""
    return {"ok": True, "receipt_save": True, "version": "receipt-v2"}


@app.post("/api/receipt")
async def analyze_receipt(file: UploadFile = File(...)):
    """Analyze a receipt image, then save extracted expense to transactions."""
    image_bytes = await file.read()
    try:
        result = analyze_receipt_image(image_bytes)
    except Exception as e:
        err = str(e).lower()
        if "insufficient_quota" in err or "billing" in err or "exceeded" in err:
            msg = "OpenAI API quota or billing limit reached. Add credits at platform.openai.com/account/billing"
        elif "rate_limit" in err:
            msg = "OpenAI rate limit hit. Wait a minute and try again."
        else:
            msg = f"Receipt analysis failed: {e}"
        return {"saved": False, "error": msg, "save_error": msg}

    if not isinstance(result, dict):
        return {
            "saved": False,
            "error": "Unexpected response from receipt analyzer",
            "save_error": "Could not parse receipt response.",
        }

    merchant = str(result.get("merchant") or "Unknown").strip()
    total = _extract_receipt_total(result)
    category = _resolve_category(merchant, result.get("category_suggestion"))
    date_str = pd.Timestamp.now().strftime("%Y-%m-%d")

    result["category"] = category
    result["amount"] = total
    result["date"] = date_str

    if total > 0:
        try:
            new_row = {
                "date": date_str,
                "merchant": merchant,
                "category": category,
                "amount": -abs(total),
                "type": "debit",
                "description": f"Receipt: {merchant}",
            }
            csv_path = os.path.join(DATA_PATH, "transactions.csv")
            pd.DataFrame([new_row]).to_csv(csv_path, mode="a", header=False, index=False)
            result["saved"] = True
            result["transaction_month"] = date_str[:7]
            result["save_error"] = None
        except Exception as e:
            result["saved"] = False
            result["save_error"] = f"Could not write to transactions file: {e}"
    else:
        result["saved"] = False
        result["save_error"] = (
            "Could not read a valid total from the receipt. "
            "Restart the backend (close FinMate Backend window, run start.bat again)."
        )

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
