"""
Canonical search families for vector filter alignment (Gemini + vector store metadata).
Maps retailer/catalog sub_category strings to a small controlled vocabulary.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

# Must match Gemini categorize_item_from_url allowed outputs exactly.
SEARCH_FAMILIES: tuple[str, ...] = (
    "Sofas",
    "Dining Chairs",
    "Side Tables",
    "Coffee Tables",
    "Arm Chairs",
    "Other",
)

SEARCH_FAMILY_PROMPT_LIST = (
    "[Sofas, Dining Chairs, Side Tables, Coffee Tables, Arm Chairs]"
)

# Exact sub_category (case-insensitive) -> search_family
_SUBCATEGORY_EXACT: dict[str, str] = {
    # Gemini / simple
    "sofas": "Sofas",
    "dining chairs": "Dining Chairs",
    "side tables": "Side Tables",
    "coffee tables": "Coffee Tables",
    "arm chairs": "Arm Chairs",
    # Efreshli-style (samples from product CSVs)
    "sofas & sectionals": "Sofas",
    "outdoor sofas": "Sofas",
    "accent & arm chairs": "Arm Chairs",
    "end & side tables": "Side Tables",
    "night tables": "Side Tables",
    "side lamps": "Other",
    "floor lamps": "Other",
    "ceiling lighting": "Other",
    "wall lights": "Other",
    "dining tables": "Other",
    "consoles & back sofas": "Sofas",
    "ottomans & benches": "Arm Chairs",
    "poufs & stools": "Arm Chairs",
    "outdoor chairs": "Dining Chairs",
    "beds": "Other",
    "dressers": "Other",
    "chests": "Other",
    "media consoles & tv units": "Side Tables",
    "dining sideboards": "Side Tables",
    "storage solutions": "Other",
    "area rugs": "Other",
    "cushions": "Other",
    "framed prints": "Other",
    "wall mirrors": "Other",
    "wall hangings": "Other",
    "baskets & bins": "Other",
    "table linens": "Other",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def map_subcategory_to_search_family(sub_category: Optional[str]) -> str:
    """
    Map a retailer or internal sub_category label to a search_family value.
    Unknown / non-furniture decor -> Other.
    """
    if not sub_category or not str(sub_category).strip():
        return "Other"
    key = _norm(str(sub_category))
    if key in _SUBCATEGORY_EXACT:
        return _SUBCATEGORY_EXACT[key]

    low = key
    if any(x in low for x in ("sofa", "sectional", "loveseat", "divan", "couch")):
        return "Sofas"
    if "coffee table" in low or low == "coffee tables":
        return "Coffee Tables"
    if any(
        x in low
        for x in (
            "side table",
            "end table",
            "night table",
            "bedside",
            "console table",
            "accent table",
        )
    ):
        return "Side Tables"
    if "dining chair" in low or ("chair" in low and "dining" in low):
        return "Dining Chairs"
    if any(
        x in low
        for x in (
            "arm chair",
            "armchair",
            "accent chair",
            "lounge chair",
            "club chair",
            "recliner",
        )
    ):
        return "Arm Chairs"
    if "chair" in low:
        return "Arm Chairs"
    if "table" in low and "coffee" not in low:
        if "dining" in low:
            return "Coffee Tables"
        return "Side Tables"

    return "Other"


def enrich_vector_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure vector store metadata includes search_family and sub_category_raw for filtering.
    Returns a sanitized copy of metadata with values flattened to str/num/bool.
    """
    out = dict(metadata) if metadata else {}
    raw = out.get("sub_category") or out.get("subCategory") or ""
    if isinstance(raw, str):
        sub_raw = raw.strip()
    else:
        sub_raw = str(raw) if raw is not None else ""

    out["sub_category_raw"] = sub_raw or ""
    out["search_family"] = map_subcategory_to_search_family(sub_raw)
    # Keep legacy sub_category aligned with canonical family for old rows; prefer raw in UI from sub_category_raw
    if sub_raw:
        out.setdefault("sub_category", sub_raw)

    sanitized: Dict[str, Any] = {}
    for k, v in out.items():
        if v is None:
            continue
        if isinstance(v, (bool, int, float)):
            sanitized[k] = v
        elif isinstance(v, str):
            sanitized[k] = v[:20000]
        else:
            sanitized[k] = str(v)[:20000]
    return sanitized
