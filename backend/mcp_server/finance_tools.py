"""
Custom MCP Server for FinMate - Personal Finance Tools.

Provides 3 financial tools:
1. categorize_expenses - Auto-categorize transactions
2. calculate_budget - Generate budget recommendations based on income
3. get_savings_plan - Create personalized savings plan with timeline
"""

import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import pandas as pd
from datetime import datetime, timedelta


app = Server("finmate-finance-tools")


CATEGORY_KEYWORDS = {
    "Groceries": ["grocery", "whole foods", "trader joe", "costco", "safeway", "walmart", "kroger", "aldi"],
    "Restaurants": ["restaurant", "cafe", "starbucks", "mcdonald", "chipotle", "uber eats", "doordash", "grubhub", "pizza"],
    "Transportation": ["uber", "lyft", "gas", "shell", "bp", "chevron", "parking", "metro", "transit"],
    "Housing": ["rent", "mortgage", "property tax", "home insurance", "hoa"],
    "Utilities": ["electric", "water", "gas bill", "internet", "phone", "mobile", "verizon", "att"],
    "Entertainment": ["netflix", "spotify", "hulu", "disney", "theater", "movie", "concert", "gaming", "steam"],
    "Shopping": ["amazon", "target", "nike", "zara", "best buy", "apple", "ikea", "nordstrom"],
    "Healthcare": ["pharmacy", "doctor", "dental", "hospital", "medical", "vision", "cvs", "walgreens"],
    "Subscriptions": ["subscription", "membership", "gym", "cloud", "premium"],
    "Income": ["salary", "payroll", "deposit", "employer", "freelance", "dividend", "interest"],
}


def categorize_transaction(description: str) -> str:
    """Categorize a single transaction based on merchant/description."""
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return "Other"


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available financial tools."""
    return [
        Tool(
            name="categorize_expenses",
            description="Automatically categorize a list of transactions based on merchant names and descriptions. Returns each transaction with an assigned spending category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "transactions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "amount": {"type": "number"},
                                "date": {"type": "string"},
                            },
                            "required": ["description", "amount"],
                        },
                        "description": "List of transactions to categorize",
                    }
                },
                "required": ["transactions"],
            },
        ),
        Tool(
            name="calculate_budget",
            description="Calculate a personalized budget allocation based on monthly income using the 50/30/20 rule with adjustments for the user's specific situation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "monthly_income": {
                        "type": "number",
                        "description": "Monthly after-tax income",
                    },
                    "fixed_expenses": {
                        "type": "number",
                        "description": "Total fixed monthly expenses (rent, insurance, etc.)",
                    },
                    "savings_goal_amount": {
                        "type": "number",
                        "description": "Target savings amount",
                    },
                    "savings_goal_months": {
                        "type": "integer",
                        "description": "Months to reach savings goal",
                    },
                },
                "required": ["monthly_income"],
            },
        ),
        Tool(
            name="get_savings_plan",
            description="Create a detailed savings plan with monthly milestones, timeline, and actionable steps based on current income, expenses, and savings goal.",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_savings": {
                        "type": "number",
                        "description": "Current savings balance",
                    },
                    "target_amount": {
                        "type": "number",
                        "description": "Target savings amount",
                    },
                    "monthly_income": {
                        "type": "number",
                        "description": "Monthly after-tax income",
                    },
                    "monthly_expenses": {
                        "type": "number",
                        "description": "Total monthly expenses",
                    },
                    "risk_tolerance": {
                        "type": "string",
                        "enum": ["conservative", "moderate", "aggressive"],
                        "description": "Risk tolerance level",
                    },
                },
                "required": ["current_savings", "target_amount", "monthly_income", "monthly_expenses"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a financial tool."""

    if name == "categorize_expenses":
        transactions = arguments["transactions"]
        categorized = []
        category_totals = {}

        for txn in transactions:
            category = categorize_transaction(txn["description"])
            categorized.append({**txn, "category": category})
            category_totals[category] = category_totals.get(category, 0) + abs(txn["amount"])

        result = {
            "categorized_transactions": categorized,
            "category_summary": {k: round(v, 2) for k, v in sorted(category_totals.items(), key=lambda x: -x[1])},
            "total_categorized": len(categorized),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "calculate_budget":
        income = arguments["monthly_income"]
        fixed = arguments.get("fixed_expenses", 0)
        goal_amount = arguments.get("savings_goal_amount", 0)
        goal_months = arguments.get("savings_goal_months", 12)

        needs_budget = income * 0.50
        wants_budget = income * 0.30
        savings_budget = income * 0.20

        if fixed > needs_budget:
            overage = fixed - needs_budget
            needs_budget = fixed
            wants_budget -= overage * 0.6
            savings_budget -= overage * 0.4

        monthly_goal_contribution = goal_amount / goal_months if goal_months > 0 else 0
        extra_savings_needed = max(0, monthly_goal_contribution - savings_budget)

        result = {
            "budget_allocation": {
                "needs (50%)": round(needs_budget, 2),
                "wants (30%)": round(wants_budget, 2),
                "savings (20%)": round(savings_budget, 2),
            },
            "detailed_needs_breakdown": {
                "housing (30% of income)": round(income * 0.30, 2),
                "utilities": round(income * 0.05, 2),
                "groceries": round(income * 0.10, 2),
                "transportation": round(income * 0.05, 2),
            },
            "savings_goal_analysis": {
                "monthly_contribution_needed": round(monthly_goal_contribution, 2),
                "current_savings_budget": round(savings_budget, 2),
                "gap": round(extra_savings_needed, 2),
                "feasible": extra_savings_needed <= wants_budget * 0.5,
            },
            "recommendations": [],
        }

        if extra_savings_needed > 0:
            result["recommendations"].append(
                f"To hit your savings goal, consider reducing wants by ${extra_savings_needed:.2f}/month"
            )
        if fixed > income * 0.5:
            result["recommendations"].append(
                "Your fixed expenses exceed 50% of income - consider reducing housing costs or increasing income"
            )

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_savings_plan":
        current = arguments["current_savings"]
        target = arguments["target_amount"]
        income = arguments["monthly_income"]
        expenses = arguments["monthly_expenses"]
        risk = arguments.get("risk_tolerance", "moderate")

        available_monthly = income - expenses
        needed = target - current

        savings_rates = {"conservative": 0.5, "moderate": 0.7, "aggressive": 0.85}
        rate = savings_rates[risk]
        monthly_savings = available_monthly * rate

        if monthly_savings <= 0:
            return [TextContent(type="text", text=json.dumps({
                "error": "Expenses exceed income - focus on reducing expenses first",
                "deficit": round(abs(available_monthly), 2),
                "suggestions": [
                    "Review subscriptions and cancel unused services",
                    "Reduce dining out expenses",
                    "Look for ways to increase income (freelance, side gig)",
                ],
            }, indent=2))]

        months_to_goal = needed / monthly_savings
        target_date = datetime.now() + timedelta(days=months_to_goal * 30)

        milestones = []
        for pct in [25, 50, 75, 100]:
            milestone_amount = current + (needed * pct / 100)
            milestone_months = (needed * pct / 100) / monthly_savings
            milestone_date = datetime.now() + timedelta(days=milestone_months * 30)
            milestones.append({
                "percentage": pct,
                "amount": round(milestone_amount, 2),
                "estimated_date": milestone_date.strftime("%Y-%m-%d"),
                "months_from_now": round(milestone_months, 1),
            })

        result = {
            "plan_summary": {
                "current_savings": current,
                "target_amount": target,
                "amount_needed": round(needed, 2),
                "monthly_savings_amount": round(monthly_savings, 2),
                "months_to_goal": round(months_to_goal, 1),
                "target_date": target_date.strftime("%Y-%m-%d"),
                "risk_profile": risk,
            },
            "milestones": milestones,
            "action_items": [
                f"Set up automatic transfer of ${monthly_savings:.2f} on payday",
                "Open a high-yield savings account (4-5% APY)",
                f"Review and adjust plan every 3 months",
                f"Available buffer: ${available_monthly - monthly_savings:.2f}/month for unexpected expenses",
            ],
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
