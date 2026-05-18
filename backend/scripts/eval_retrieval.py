#!/usr/bin/env python3
"""
Offline retrieval evaluation: Recall@K and MRR with optional Pinecone metadata filters.

Usage (from repo root):
  cd backend && python scripts/eval_retrieval.py --manifest ../data/eval_manifest.example.json

Requires .env with PINECONE_API_KEY, PINECONE_INDEX_NAME, and optionally MODEL_PRESET / CUDA.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Set

# Allow running as script from backend/
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(_BACKEND_DIR, ".env"))
load_dotenv()


def recall_at_k(ranked_ids: List[str], relevant: Set[str], k: int) -> float:
    if not relevant:
        return 0.0
    top = ranked_ids[:k]
    hits = sum(1 for x in top if x in relevant)
    return hits / len(relevant) if relevant else 0.0


def mrr(ranked_ids: List[str], relevant: Set[str]) -> float:
    for i, vid in enumerate(ranked_ids, start=1):
        if vid in relevant:
            return 1.0 / i
    return 0.0


def run_eval(
    manifest_path: str,
    k_list: List[int],
    preset: Optional[str],
    no_filter: bool,
    multi_crop: bool,
) -> Dict[str, Any]:
    import torch
    from pinecone import Pinecone

    from image_embedder3 import ImageEmbedder3
    from retrieval import pinecone_filter_search_family

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_preset = preset or os.getenv("MODEL_PRESET", "balanced")
    embedder = ImageEmbedder3(preset=model_preset, device=device)

    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index_name = os.getenv("PINECONE_INDEX_NAME", "default")
    index = pc.Index(index_name)

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    queries: List[Dict[str, Any]] = manifest.get("queries") or []

    max_k = max(k_list) if k_list else 10
    agg_filtered = {k: [] for k in k_list}
    agg_unfiltered = {k: [] for k in k_list}
    mrr_f: List[float] = []
    mrr_u: List[float] = []
    evaluated = 0

    for q in queries:
        url = q.get("image_url")
        rel = set(q.get("relevant_ids") or [])
        family = q.get("search_family")
        if not url:
            continue

        vec = embedder.get_embedding(url, multi_crop=multi_crop)
        if vec is None:
            print(f"SKIP embed failed: {url}")
            continue
        vec_list = vec.tolist() if hasattr(vec, "tolist") else list(vec)

        def do_query(filter_dict: Optional[Dict[str, Any]]) -> List[str]:
            kwargs: Dict[str, Any] = {
                "vector": vec_list,
                "top_k": max_k,
                "include_metadata": True,
                "namespace": os.getenv("PINECONE_NAMESPACE", "__default__"),
            }
            if filter_dict is not None:
                kwargs["filter"] = filter_dict
            resp = index.query(**kwargs)
            return [m["id"] for m in (resp.get("matches") or [])]

        filt = None
        if not no_filter and family:
            filt = pinecone_filter_search_family(str(family), "exact")

        ids_unfiltered = do_query(None)
        if no_filter:
            ids_filtered = ids_unfiltered
        else:
            ids_filtered = do_query(filt)

        for kk in k_list:
            agg_filtered[kk].append(recall_at_k(ids_filtered, rel, kk))
            agg_unfiltered[kk].append(recall_at_k(ids_unfiltered, rel, kk))
        mrr_f.append(mrr(ids_filtered, rel))
        mrr_u.append(mrr(ids_unfiltered, rel))
        evaluated += 1

    def mean(xs: List[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    return {
        "num_manifest_queries": len(queries),
        "num_evaluated": evaluated,
        "model_preset": model_preset,
        "multi_crop": multi_crop,
        "no_filter_mode": no_filter,
        "recall_at_k_filtered": {str(k): mean(agg_filtered[k]) for k in k_list},
        "recall_at_k_unfiltered": {str(k): mean(agg_unfiltered[k]) for k in k_list},
        "mrr_filtered": mean(mrr_f),
        "mrr_unfiltered": mean(mrr_u),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="VisionFFE retrieval eval")
    p.add_argument("--manifest", required=True, help="Path to eval manifest JSON")
    p.add_argument("--k", default="1,5,10", help="Comma-separated K values for Recall@K")
    p.add_argument("--preset", default=None, help="Override MODEL_PRESET for OpenCLIP")
    p.add_argument("--no-filter", action="store_true", help="Do not apply search_family metadata filter (filtered metrics mirror unfiltered)")
    p.add_argument("--multi-crop", action="store_true", help="Use embedder multi-crop averaging")
    args = p.parse_args()
    k_list = [int(x.strip()) for x in args.k.split(",") if x.strip()]

    if "PINECONE_API_KEY" not in os.environ:
        print("ERROR: PINECONE_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    report = run_eval(
        args.manifest,
        k_list=k_list,
        preset=args.preset,
        no_filter=args.no_filter,
        multi_crop=args.multi_crop,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
