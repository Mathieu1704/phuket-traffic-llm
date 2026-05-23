"""
Query router + multi-collection ChromaDB retriever.
Returns a list of {"text": ..., "metadata": {...}} dicts.
Falls back gracefully if ChromaDB is not yet populated (before ingest.py is run).
"""
import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 5

# Collections selected per detected intent keyword
ROUTING_TABLE = {
    "traffic": ["traffic_monthly", "traffic_segments"],
    "congestion": ["traffic_monthly", "traffic_segments"],
    "travel time": ["traffic_monthly", "traffic_segments"],
    "speed": ["traffic_monthly", "traffic_segments"],
    "slow": ["traffic_monthly", "traffic_segments"],
    "fast": ["traffic_monthly", "traffic_segments"],
    "intersection": ["intersections", "turning_movements"],
    "junction": ["intersections", "turning_movements"],
    "turning": ["turning_movements"],
    "vehicles": ["turning_movements"],
    "flight": ["flights", "traffic_monthly"],
    "airport": ["flights", "traffic_monthly"],
    "passenger": ["flights", "traffic_monthly"],
    "pax": ["flights", "traffic_monthly"],
    "weather": ["weather", "traffic_monthly"],
    "rain": ["weather", "traffic_monthly"],
    "temperature": ["weather", "traffic_monthly"],
    "monsoon": ["weather", "traffic_monthly"],
    "event": ["events", "traffic_monthly"],
    "festival": ["events", "traffic_monthly"],
    "songkran": ["events", "traffic_monthly"],
    "holiday": ["events", "traffic_monthly"],
    "market": ["events"],
    "trend": ["social_trends"],
    "google": ["social_trends"],
    "search": ["social_trends"],
    "hotel": ["poi", "intersections"],
    "beach": ["poi", "intersections"],
    "restaurant": ["poi"],
    "poi": ["poi"],
    "bus": ["transport"],
    "ferry": ["transport"],
    "transport": ["transport"],
    "route": ["transport"],
}

DEFAULT_COLLECTIONS = ["traffic_monthly", "events", "flights"]

# Collections never useful for simple traffic questions (too much noise)
NOISY_FOR_TRAFFIC = {"traffic_segments"}

_client = None
_embed_fn = None


def _get_client():
    global _client, _embed_fn
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _embed_fn = SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    return _client, _embed_fn


def _select_collections(query: str) -> list[str]:
    query_lower = query.lower()
    selected = set()
    for keyword, collections in ROUTING_TABLE.items():
        if keyword in query_lower:
            selected.update(collections)
    if not selected:
        selected = set(DEFAULT_COLLECTIONS)
    # If query mentions a specific month/year, prefer traffic_monthly over segments
    import re
    if re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b', query_lower):
        selected.discard("traffic_segments")
        selected.add("traffic_monthly")
    # max 3 collections to keep context manageable
    return list(selected)[:3]


MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _extract_date_filter(query: str) -> dict:
    import re
    q = query.lower()
    filters = {}
    for name, num in MONTH_MAP.items():
        if name in q:
            filters["month"] = num
            break
    year_match = re.search(r'\b(202[2-5])\b', q)
    if year_match:
        filters["year"] = int(year_match.group(1))
    return filters


def retrieve_context(query: str, corridor_id: int = -1) -> list[dict]:
    try:
        client, embed_fn = _get_client()
        collections_to_query = _select_collections(query)
        date_filter = _extract_date_filter(query)

        results = []
        for coll_name in collections_to_query:
            try:
                coll = client.get_collection(name=coll_name, embedding_function=embed_fn)

                # Build where clause: combine corridor + date filters when available
                conditions = []
                if corridor_id >= 0:
                    conditions.append({"corridor_id": {"$eq": corridor_id}})
                if "year" in date_filter and coll_name in ("traffic_monthly", "flights", "weather", "social_trends"):
                    conditions.append({"year": {"$eq": date_filter["year"]}})
                if "month" in date_filter and coll_name in ("traffic_monthly", "flights", "weather"):
                    conditions.append({"month": {"$eq": date_filter["month"]}})

                if len(conditions) > 1:
                    where = {"$and": conditions}
                elif len(conditions) == 1:
                    where = conditions[0]
                else:
                    where = None

                res = coll.query(query_texts=[query], n_results=TOP_K, where=where)
                docs = res["documents"][0]

                # Fall back to unfiltered only if zero results
                if len(docs) < 1 and where is not None:
                    res = coll.query(query_texts=[query], n_results=TOP_K)
                    docs = res["documents"][0]

                for text, meta in zip(docs, res["metadatas"][0]):
                    results.append({"text": text, "metadata": meta})
            except Exception:
                pass

        return results

    except Exception:
        return []
