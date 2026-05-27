"""
Guardrails for FinMate - Input/Output safety filtering.

1. PII Detection & Masking: Prevents leaking credit card numbers, SSNs, account numbers
2. Prompt Injection Detection: Blocks attempts to override system prompts
3. Domain Boundary Enforcement: Keeps responses within personal finance domain
"""

import re
from typing import Tuple


PII_PATTERNS = {
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
    "account_number": r"\b\d{8,17}\b",
    "routing_number": r"\b\d{9}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
}

INJECTION_PATTERNS = [
    r"ignore (?:all )?(?:previous|above|prior) (?:instructions|prompts)",
    r"you are now",
    r"new instructions:",
    r"system prompt:",
    r"forget (?:everything|all|your)",
    r"pretend (?:you are|to be)",
    r"override (?:your|the) (?:instructions|rules|guidelines)",
    r"disregard (?:your|the|all)",
]

OFF_TOPIC_INDICATORS = [
    "write me a poem",
    "tell me a joke about",
    "help me with my homework",
    "write code for",
    "translate this",
    "what's the weather",
    "recipe for",
    "who won the",
]


def detect_pii(text: str) -> dict:
    """Detect PII in text and return findings."""
    findings = {}
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            findings[pii_type] = len(matches)
    return findings


def mask_pii(text: str) -> str:
    """Mask detected PII in text."""
    masked = text
    masked = re.sub(PII_PATTERNS["credit_card"], "****-****-****-XXXX", masked)
    masked = re.sub(PII_PATTERNS["ssn"], "***-**-XXXX", masked)
    masked = re.sub(PII_PATTERNS["email"], "[EMAIL REDACTED]", masked)
    return masked


def detect_prompt_injection(text: str) -> bool:
    """Check if input contains prompt injection attempts."""
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in INJECTION_PATTERNS)


def check_domain_relevance(text: str) -> bool:
    """Check if the query is within the personal finance domain."""
    text_lower = text.lower()
    finance_keywords = [
        "money", "budget", "spend", "save", "income", "expense", "debt",
        "invest", "finance", "bank", "credit", "loan", "payment", "bill",
        "salary", "tax", "retire", "fund", "goal", "net worth", "mortgage",
        "receipt", "transaction", "account", "subscription", "grocery",
    ]

    if any(kw in text_lower for kw in finance_keywords):
        return True

    if any(indicator in text_lower for indicator in OFF_TOPIC_INDICATORS):
        return False

    return True  # Default: allow (the LLM can handle borderline cases)


def validate_input(text: str) -> Tuple[bool, str, str]:
    """
    Validate user input. Returns (is_safe, cleaned_text, warning_message).
    """
    if detect_prompt_injection(text):
        return False, "", "I detected a prompt that's outside my scope. I'm here to help with personal finance questions!"

    pii_found = detect_pii(text)
    cleaned_text = mask_pii(text) if pii_found else text

    warning = ""
    if pii_found:
        warning = "I noticed some sensitive information in your message and have masked it for your safety."

    return True, cleaned_text, warning


def validate_output(text: str) -> str:
    """Validate and clean LLM output before showing to user."""
    cleaned = mask_pii(text)

    disclaimers_needed = any(
        kw in text.lower()
        for kw in ["invest in", "buy stock", "specific investment", "guarantee"]
    )

    if disclaimers_needed and "not financial advice" not in text.lower():
        cleaned += "\n\n*Note: This is educational guidance, not professional financial advice. Please consult a licensed financial advisor for investment decisions.*"

    return cleaned
