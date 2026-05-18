"""
Two-stage retrieval helpers: Pinecone query, score thresholding, family fallback, metadata re-ranking.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

# Widen filter if first query is sparse
RELATED_SEARCH_FAMILIES: Dict[str, List[str]] = {
    "Sofas": ["Sofas", "Arm Chairs"],
    "Arm Chairs": ["Arm Chairs", "Sofas", "Dining Chairs"],
    "Dining Chairs": ["Dining Chairs", "Arm Chairs"],
    "Coffee Tables": ["Coffee Tables", "Side Tables"],
    "Side Tables": ["Side Tables", "Coffee Tables"],
}

_FAMILY_KEYWORDS: Dict[str, List[str]] = {
    "Sofas": ["sofa", "sectional", "couch", "loveseat", "divan", "upholster"],
    "Dining Chairs": ["dining", "chair", "seat", "wooden chair"],
    "Side Tables": ["side", "end", "night", "bedside", "console", "accent table"],
    "Coffee Tables": ["coffee", "table", "living"],
    "Arm Chairs": ["arm", "accent", "lounge", "club", "recliner", "chair"],
}


def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


def similarity_threshold() -> Optional[float]:
    """
    Minimum Pinecone similarity score to keep a hit. None = no cutoff.
    Set SIMILARITY_THRESHOLD=-1 to disable.
    """
    raw = os.getenv("SIMILARITY_THRESHOLD", "0.35")
    if raw.strip() == "":
        return None
    try:
        v = float(raw)
        if v < 0:
            return None
        return v
    except ValueError:
        return 0.35


def internal_candidate_k(requested_top_k: int) -> int:
    """How many vectors to retrieve before re-rank / threshold."""
    cap = _env_int("RETRIEVAL_CANDIDATES_K", 50)
    return min(max(requested_top_k, cap), 100)


def min_results_before_fallback() -> int:
    return _env_int("RETRIEVAL_MIN_RESULTS_FALLBACK", 2)


def pinecone_filter_search_family(
    family: str, mode: str = "exact"
) -> Optional[Dict[str, Any]]:
    if mode == "exact":
        return {"search_family": {"$eq": family}}
    if mode == "related":
        related = RELATED_SEARCH_FAMILIES.get(family, [family])
        return {"search_family": {"$in": related}}
    return None


def query_pinecone_with_fallback(
    pinecone_index,
    vector: List[float],
    search_family: str,
    top_k: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Query Pinecone: exact family -> related families -> no metadata filter.
    Returns (matches list compatible with Pinecone 'matches' shape, debug dict).
    """
    debug: Dict[str, Any] = {"stages": []}
    internal_k = internal_candidate_k(top_k)

    def run_query(filter_dict: Optional[Dict[str, Any]], label: str) -> List[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {
            "vector": vector,
            "top_k": internal_k,
            "include_metadata": True,
        }
        if filter_dict is not None:
            kwargs["filter"] = filter_dict
        kwargs["namespace"] = os.getenv("PINECONE_NAMESPACE", "__default__")
        resp = pinecone_index.query(**kwargs)
        matches = list(resp.get("matches") or [])
        debug["stages"].append({"stage": label, "filter": filter_dict, "count": len(matches)})
        return matches

    f_exact = pinecone_filter_search_family(search_family, "exact")
    matches = run_query(f_exact, "exact_family")

    if len(matches) < min_results_before_fallback():
        f_rel = pinecone_filter_search_family(search_family, "related")
        matches = run_query(f_rel, "related_families")

    if len(matches) < min_results_before_fallback():
        matches = run_query(None, "no_filter")

    return matches, debug


def rerank_matches_by_category_keywords(
    matches: List[Dict[str, Any]],
    gemini_family: str,
) -> List[Dict[str, Any]]:
    """
    Light re-ranker: boost score slightly when title/description contains family keywords.
    Does not remove items; preserves relative order on ties.
    """
    keywords = _FAMILY_KEYWORDS.get(gemini_family, [])
    if not keywords:
        return matches

    boost = _env_float("RETRIEVAL_METADATA_BOOST", 0.04)

    def meta_text(m: Dict[str, Any]) -> str:
        meta = m.get("metadata") or {}
        parts = [
            str(meta.get("title", "")),
            str(meta.get("description", "")),
            str(meta.get("sub_category_raw", "")),
            str(meta.get("sub_category", "")),
        ]
        return " ".join(parts)

    scored: List[Tuple[float, int, Dict[str, Any]]] = []
    for i, m in enumerate(matches):
        base = float(m.get("score", 0.0))
        text = meta_text(m)
        extra = 0.0
        if any(kw in text.lower() for kw in keywords):
            extra = boost
        scored.append((base + extra, i, m))

    scored.sort(key=lambda x: (-x[0], x[1]))
    out: List[Dict[str, Any]] = []
    for s, _i, m in scored:
        row = dict(m)
        row["score"] = s
        row["rerank_score"] = s
        out.append(row)
    return out


def apply_similarity_threshold(
    matches: List[Dict[str, Any]], threshold: Optional[float]
) -> List[Dict[str, Any]]:
    if threshold is None:
        return matches
    return [m for m in matches if float(m.get("score", 0.0)) >= threshold]


def trim_to_top_k(matches: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    return matches[: max(0, top_k)]
