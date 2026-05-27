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
    """Process a chat message through the finance agent."""
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
        user_message=msg.message,
        transaction_data=summary,
        user_profile=json.dumps(profile),
        chat_history=chat_history,
    )

    return {
        "response": result["response"],
        "intent": result["intent"],
    }


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


@app.post("/api/receipt")
async def analyze_receipt(file: UploadFile = File(...)):
    """Analyze a receipt image."""
    image_bytes = await file.read()
    result = analyze_receipt_image(image_bytes)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
