"""Offers educational, risk-tolerance-appropriate investment direction via RAG."""
from app.db import UserProfile
from app.rag.knowledge_base import query_tips


class InvestmentAgent:
    DISCLAIMER = (
        "This is general educational guidance, not licensed financial advice. "
        "Consult a certified financial advisor before making investment decisions."
    )

    def guidance(self, profile: UserProfile) -> dict:
        query = f"{profile.risk_tolerance} risk tolerance investment allocation"
        tips = query_tips(query, n_results=2)

        return {
            "risk_tolerance": profile.risk_tolerance,
            "guidance": tips,
            "disclaimer": self.DISCLAIMER,
        }
