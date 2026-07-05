"""Parses natural-language expense entries into structured, categorized transactions."""
import re

from app.llm import call_llm_json, llm_available

CATEGORIES = [
    "groceries", "rent", "utilities", "transport", "dining_out",
    "entertainment", "healthcare", "shopping", "subscriptions",
    "debt_payment", "savings", "other",
]

# Simple keyword fallback if no LLM is configured
KEYWORD_MAP = {
    "groceries": ["grocery", "groceries", "supermarket", "vegetables", "milk"],
    "rent": ["rent", "landlord"],
    "utilities": ["electricity", "water bill", "internet", "wifi", "gas bill"],
    "transport": ["uber", "ola", "petrol", "fuel", "bus", "train", "cab", "auto"],
    "dining_out": ["restaurant", "swiggy", "zomato", "cafe", "coffee", "lunch", "dinner out"],
    "entertainment": ["movie", "netflix", "game", "concert"],
    "healthcare": ["medicine", "doctor", "hospital", "pharmacy"],
    "shopping": ["amazon", "flipkart", "clothes", "shoes", "shopping"],
    "subscriptions": ["subscription", "prime", "spotify"],
    "debt_payment": ["emi", "loan payment", "credit card bill"],
    "savings": ["savings", "fd", "recurring deposit", "invested"],
}

AMOUNT_RE = re.compile(r"[₹$]?\s?(\d+(?:[.,]\d+)?)")


class CategorizationAgent:
    def categorize(self, text: str) -> dict:
        if llm_available():
            try:
                return self._categorize_llm(text)
            except Exception:
                pass  # fall through to rule-based
        return self._categorize_rule_based(text)

    def _categorize_llm(self, text: str) -> dict:
        system = (
            "You are an expense categorization agent for a budgeting app. "
            f"Categorize the expense into exactly one of: {', '.join(CATEGORIES)}. "
            "Extract the numeric amount. Return JSON: {\"category\": str, \"amount\": float}."
        )
        result = call_llm_json(system, text, max_tokens=150)
        if result.get("category") not in CATEGORIES:
            result["category"] = "other"
        return result

    def _categorize_rule_based(self, text: str) -> dict:
        lower = text.lower()
        category = "other"
        for cat, keywords in KEYWORD_MAP.items():
            if any(kw in lower for kw in keywords):
                category = cat
                break

        match = AMOUNT_RE.search(text)
        amount = float(match.group(1).replace(",", "")) if match else 0.0

        return {"category": category, "amount": amount}
