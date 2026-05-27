"""
Multimodal receipt/statement analyzer using GPT-4o Vision.
Analyzes images of receipts, bank statements, or financial documents
and extracts structured transaction data.
"""

import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from backend.utils.config import OPENAI_API_KEY, DEFAULT_MODEL


def encode_image(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def analyze_receipt_image(image_bytes: bytes) -> dict:
    """
    Analyze a receipt or financial document image using GPT-4o Vision.
    Returns structured data extracted from the image.
    """
    llm = ChatOpenAI(
        model=DEFAULT_MODEL,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=1500,
        temperature=0.1,
    )

    base64_image = encode_image(image_bytes)

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": """Analyze this financial document image (receipt, bank statement, or invoice).
Extract and return a JSON object with:
{
    "document_type": "receipt" | "bank_statement" | "invoice" | "other",
    "merchant": "store/business name",
    "date": "YYYY-MM-DD format if visible",
    "items": [{"description": "item name", "amount": 0.00}],
    "subtotal": 0.00,
    "tax": 0.00,
    "total": 0.00,
    "payment_method": "cash/card/other if visible",
    "category_suggestion": "suggested spending category",
    "notes": "any additional relevant information"
}
Return ONLY valid JSON, no markdown formatting.""",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high",
                },
            },
        ]
    )

    response = llm.invoke([message])

    import json
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = {
                "document_type": "unknown",
                "raw_analysis": response.content,
                "error": "Could not parse structured data",
            }

    return result


def analyze_statement_image(image_bytes: bytes) -> dict:
    """
    Analyze a bank statement image and extract transaction list.
    Optimized for statement-format documents with multiple transactions.
    """
    llm = ChatOpenAI(
        model=DEFAULT_MODEL,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=2000,
        temperature=0.1,
    )

    base64_image = encode_image(image_bytes)

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": """Analyze this bank statement image and extract all visible transactions.
Return a JSON object:
{
    "account_holder": "name if visible",
    "statement_period": "date range if visible",
    "transactions": [
        {"date": "YYYY-MM-DD", "description": "merchant/description", "amount": -0.00, "category": "suggested category"}
    ],
    "opening_balance": 0.00,
    "closing_balance": 0.00,
    "total_debits": 0.00,
    "total_credits": 0.00
}
Use negative amounts for debits/expenses, positive for credits/income.
Return ONLY valid JSON.""",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high",
                },
            },
        ]
    )

    response = llm.invoke([message])

    import json
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = {"raw_analysis": response.content, "error": "Could not parse"}

    return result
