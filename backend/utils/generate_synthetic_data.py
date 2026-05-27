"""
Generate realistic synthetic personal finance transaction data.
Creates a 6-month transaction history for a fictional user profile.
Ensures consistent monthly expenses (rent, utilities, subscriptions).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import os


# Fixed monthly expenses - these happen EVERY month consistently
FIXED_MONTHLY = [
    {"merchant": "Rent Payment", "category": "Housing", "amount": -1600, "day": 1},
    {"merchant": "Electric Company", "category": "Utilities", "amount": -85, "day": 5},
    {"merchant": "Internet Provider", "category": "Utilities", "amount": -65, "day": 8},
    {"merchant": "Mobile Carrier", "category": "Utilities", "amount": -55, "day": 10},
    {"merchant": "Water Utility", "category": "Utilities", "amount": -35, "day": 12},
    {"merchant": "Netflix", "category": "Subscriptions", "amount": -15.99, "day": 3},
    {"merchant": "Spotify", "category": "Subscriptions", "amount": -10.99, "day": 7},
    {"merchant": "Gym Membership", "category": "Subscriptions", "amount": -45, "day": 1},
    {"merchant": "Cloud Storage", "category": "Subscriptions", "amount": -9.99, "day": 15},
]

# Income - biweekly
INCOME = [
    {"merchant": "Employer - TechCorp Inc", "category": "Income", "amount": 2900, "days": [1, 15]},
]

# Variable expenses - randomized per week/month
VARIABLE_EXPENSES = {
    "Groceries": {
        "merchants": ["Whole Foods", "Trader Joe's", "Costco", "Safeway", "Target"],
        "per_month": (6, 10),
        "amount_range": (25, 145),
    },
    "Restaurants": {
        "merchants": ["Chipotle", "Starbucks", "McDonald's", "Local Bistro", "Uber Eats", "DoorDash", "Pizza Hut", "Sushi Place"],
        "per_month": (8, 14),
        "amount_range": (8, 55),
    },
    "Transportation": {
        "merchants": ["Shell Gas", "Uber", "Lyft", "City Parking", "BP Gas Station"],
        "per_month": (4, 8),
        "amount_range": (12, 65),
    },
    "Entertainment": {
        "merchants": ["AMC Theaters", "Steam Games", "Concert Venue", "Bowling Alley", "Book Store"],
        "per_month": (2, 5),
        "amount_range": (15, 95),
    },
    "Shopping": {
        "merchants": ["Amazon", "Nike", "Zara", "Best Buy", "IKEA", "Apple Store", "Target"],
        "per_month": (2, 5),
        "amount_range": (20, 250),
    },
    "Healthcare": {
        "merchants": ["City Pharmacy", "Dr. Smith Office", "Dental Care"],
        "per_month": (0, 2),
        "amount_range": (15, 150),
    },
}


def generate_transactions(months: int = 6, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic transaction data for a specified number of months."""
    random.seed(seed)
    np.random.seed(seed)

    end_date = datetime(2026, 5, 26)
    # Generate 7 months to ensure we have full data for 6 months including current
    total_months = months + 1
    start_month = end_date.month - months
    start_year = end_date.year
    if start_month <= 0:
        start_month += 12
        start_year -= 1

    transactions = []

    # Generate month by month (including current month)
    for m_offset in range(total_months):
        month = start_month + m_offset
        year = start_year
        if month > 12:
            month -= 12
            year += 1

        days_in_month = 28 if month == 2 else (30 if month in [4, 6, 9, 11] else 31)

        # Fixed monthly expenses (consistent every month)
        for expense in FIXED_MONTHLY:
            day = min(expense["day"], days_in_month)
            # Add small variation to utilities (±10%)
            amount = expense["amount"]
            if expense["category"] == "Utilities":
                amount = round(amount * random.uniform(0.9, 1.1), 2)

            transactions.append({
                "date": f"{year}-{month:02d}-{day:02d}",
                "merchant": expense["merchant"],
                "category": expense["category"],
                "amount": amount,
                "type": "debit",
                "description": f"Payment to {expense['merchant']}",
            })

        # Income (1st and 15th)
        for inc in INCOME:
            for day in inc["days"]:
                transactions.append({
                    "date": f"{year}-{month:02d}-{day:02d}",
                    "merchant": inc["merchant"],
                    "category": inc["category"],
                    "amount": inc["amount"],
                    "type": "credit",
                    "description": f"Payment from {inc['merchant']}",
                })

        # Variable expenses
        for category, config in VARIABLE_EXPENSES.items():
            num_txns = random.randint(*config["per_month"])
            for _ in range(num_txns):
                day = random.randint(1, min(days_in_month, 28))
                # Don't generate future dates
                txn_date = datetime(year, month, day)
                if txn_date > end_date:
                    continue

                merchant = random.choice(config["merchants"])
                amount = -round(random.uniform(*config["amount_range"]), 2)

                transactions.append({
                    "date": f"{year}-{month:02d}-{day:02d}",
                    "merchant": merchant,
                    "category": category,
                    "amount": amount,
                    "type": "debit",
                    "description": f"Payment to {merchant}",
                })

    df = pd.DataFrame(transactions)
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df


def generate_user_profile() -> dict:
    """Generate a fictional user profile for the demo."""
    return {
        "name": "Alex Johnson",
        "age": 29,
        "occupation": "Software Engineer",
        "monthly_income": 5800,
        "savings_goal": 15000,
        "current_savings": 4200,
        "financial_goals": [
            "Build 6-month emergency fund",
            "Save for down payment on apartment",
            "Reduce dining out expenses by 30%",
        ],
        "risk_tolerance": "moderate",
    }


def save_data(output_dir: str = None):
    """Generate and save all synthetic data."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_transactions")

    os.makedirs(output_dir, exist_ok=True)

    df = generate_transactions(months=6)
    df.to_csv(os.path.join(output_dir, "transactions.csv"), index=False)

    profile = generate_user_profile()
    with open(os.path.join(output_dir, "user_profile.json"), "w") as f:
        json.dump(profile, f, indent=2)

    print(f"Generated {len(df)} transactions over 6 months")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Categories: {df['category'].nunique()}")

    expenses = df[df["amount"] < 0]
    print(f"\nMonthly breakdown:")
    for month in sorted(expenses["date"].str[:7].unique()):
        month_data = expenses[expenses["date"].str.startswith(month)]
        total = month_data["amount"].sum()
        housing = month_data[month_data["category"] == "Housing"]["amount"].sum()
        print(f"  {month}: Total ${abs(total):,.0f} | Housing: ${abs(housing):,.0f}")

    return df, profile


if __name__ == "__main__":
    save_data()
