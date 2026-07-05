"""Seeds and queries a ChromaDB collection of financial guidance content for RAG.

ChromaDB is treated as fully optional. If it isn't installed (e.g. no C++ build
tools available to compile its dependencies on Windows) or its embedding model
can't be downloaded, this module transparently falls back to static tips so the
rest of the app keeps working without any RAG features.
"""
_collection = None
try:
    import chromadb
    _client = chromadb.PersistentClient(path="./chroma_data")
    _collection = _client.get_or_create_collection(name="financial_tips")
except Exception as e:
    print(f"[knowledge_base] ChromaDB unavailable, RAG disabled, using static tips: {e}")

SEED_DOCS = [
    {
        "id": "tip_1",
        "text": "For low risk tolerance, prioritize an emergency fund covering 6 months of "
                "expenses before any market investing. Consider fixed deposits or debt mutual funds.",
        "tags": "low_risk emergency_fund",
    },
    {
        "id": "tip_2",
        "text": "For moderate risk tolerance, a common starting allocation is 60% equity index "
                "funds, 30% debt instruments, 10% liquid/emergency reserves, adjusted with age.",
        "tags": "moderate_risk allocation",
    },
    {
        "id": "tip_3",
        "text": "For high risk tolerance and a long time horizon, higher equity exposure "
                "(70-85%) can be appropriate, but should still be paired with a fully funded "
                "emergency fund first.",
        "tags": "high_risk allocation",
    },
    {
        "id": "tip_4",
        "text": "The debt avalanche method (highest interest rate first) minimizes total interest "
                "paid over time and is mathematically optimal for debt payoff.",
        "tags": "debt avalanche",
    },
    {
        "id": "tip_5",
        "text": "The debt snowball method (smallest balance first) builds momentum through quick "
                "wins and can improve adherence for people who struggle with motivation.",
        "tags": "debt snowball",
    },
    {
        "id": "tip_6",
        "text": "A healthy debt-to-income ratio is generally below 36%, with housing costs ideally "
                "under 28% of gross monthly income.",
        "tags": "debt_ratio housing",
    },
    {
        "id": "tip_7",
        "text": "Automating transfers to savings on payday (paying yourself first) is more effective "
                "than saving whatever is left over at month end.",
        "tags": "savings automation",
    },
]


def seed_knowledge_base():
    """Seed the collection. No-ops safely if ChromaDB isn't available or the
    embedding model can't be downloaded (e.g. no network access) so the rest
    of the app still runs."""
    if _collection is None:
        return
    try:
        existing = _collection.get()["ids"]
        to_add = [d for d in SEED_DOCS if d["id"] not in existing]
        if to_add:
            _collection.add(
                ids=[d["id"] for d in to_add],
                documents=[d["text"] for d in to_add],
                metadatas=[{"tags": d["tags"]} for d in to_add],
            )
    except Exception as e:
        print(f"[knowledge_base] Seeding skipped (embedding model unavailable): {e}")


def query_tips(query: str, n_results: int = 3) -> list[str]:
    """Query the RAG collection. Falls back to static tips if ChromaDB isn't
    available or the query fails for any reason."""
    if _collection is None:
        return _fallback_tips()
    try:
        results = _collection.query(query_texts=[query], n_results=n_results)
        docs = results.get("documents", [[]])
        return docs[0] if docs and docs[0] else _fallback_tips()
    except Exception as e:
        print(f"[knowledge_base] Query failed, using fallback tips: {e}")
        return _fallback_tips()


def _fallback_tips() -> list[str]:
    return [d["text"] for d in SEED_DOCS[:2]]
