#!/usr/bin/env python3
"""
Bulk ingest images -> embeddings -> Pinecone, for testing an embedding backend.

Feeds images from the real catalog CSV (default), a local folder, or a URL list,
embeds each with the selected backend (Gemini Embedding 2 by default), enriches
metadata with the shared taxonomy, and upserts into a Pinecone index (created if
missing). Pair with scripts/eval_retrieval.py to compare backends.

Usage (from repo root):
  cd backend
  python scripts/ingest_embeddings.py --backend gemini --source csv \
      --path ../data/efreshli-products.csv --limit 50 --index visionffe-gemini-test

  python scripts/ingest_embeddings.py --backend gemini --source folder --path ./imgs
  python scripts/ingest_embeddings.py --backend gemini --source urls --path urls.txt

Requires .env with GEMINI_API_KEY (gemini) or MODEL_PRESET (openclip), plus
PINECONE_API_KEY. GEMINI_EMBED_DIM controls both the Gemini output dim and the
index dimension for a newly created index.
"""

from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import os
import sys
import time
import uuid
from typing import Any, Dict, Iterator, List, Optional, Tuple

# Allow running as a script from backend/
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(_BACKEND_DIR, ".env"))
load_dotenv()

from embedder_factory import create_embedder  # noqa: E402
from taxonomy import enrich_pinecone_metadata  # noqa: E402


def _default_dim() -> int:
    raw = os.getenv("GEMINI_EMBED_DIM", "1536")
    try:
        return int(raw)
    except ValueError:
        return 1536


def iter_csv(path: str) -> Iterator[Dict[str, Any]]:
    """Yield {url, metadata} rows from an Efreshli-style product CSV."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = (row.get("image_url") or "").strip()
            if not url:
                continue
            meta = {
                "title": row.get("title", ""),
                "description": row.get("description", ""),
                "category": row.get("category", ""),
                "sub_category": row.get("sub_category", ""),
                "brand": row.get("brand", ""),
                "sku": row.get("sku", ""),
                "price": row.get("price", ""),
                "image_url": url,
            }
            yield {"url": url, "id": row.get("sku") or None, "metadata": meta}


def iter_urls(path: str) -> Iterator[Dict[str, Any]]:
    """Yield rows from a newline- or JSON-list of image URLs."""
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()
    urls: List[str]
    try:
        parsed = json.loads(content)
        urls = parsed if isinstance(parsed, list) else [str(parsed)]
    except json.JSONDecodeError:
        urls = [line.strip() for line in content.splitlines() if line.strip()]
    for url in urls:
        yield {"url": url, "id": None, "metadata": {"image_url": url}}


def iter_folder(path: str) -> Iterator[Dict[str, Any]]:
    """Yield local image files as {bytes, mime, metadata}."""
    exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        if not os.path.isfile(full):
            continue
        if os.path.splitext(name)[1].lower() not in exts:
            continue
        with open(full, "rb") as f:
            data = f.read()
        mime = mimetypes.guess_type(full)[0] or "image/jpeg"
        yield {
            "bytes": data,
            "mime": mime,
            "id": os.path.splitext(name)[0],
            "metadata": {"title": name, "filename": name},
        }


def ensure_index(pc, index_name: str, dim: int):
    """Return the index handle, creating a serverless cosine index if missing."""
    existing = pc.list_indexes().names()
    if index_name not in existing:
        from pinecone import ServerlessSpec

        cloud = os.getenv("PINECONE_CLOUD", "aws")
        region = os.getenv("PINECONE_REGION", "us-east-1")
        print(f"Creating Pinecone index '{index_name}' (dim={dim}, metric=cosine, {cloud}/{region})...")
        pc.create_index(
            name=index_name,
            dimension=dim,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )
        # Wait for readiness
        for _ in range(30):
            if index_name in pc.list_indexes().names():
                break
            time.sleep(2)
    return pc.Index(index_name)


def _embed_row(embedder, row: Dict[str, Any]):
    """Embed either a URL row or an in-memory bytes row."""
    if "bytes" in row:
        if hasattr(embedder, "embed_bytes"):
            return embedder.embed_bytes(row["bytes"], row.get("mime", "image/jpeg"))
        raise RuntimeError(
            "Selected backend cannot embed raw bytes (folder source); use --source csv/urls."
        )
    return embedder.get_embedding(row["url"])


def run(args: argparse.Namespace) -> int:
    from pinecone import Pinecone

    if "PINECONE_API_KEY" not in os.environ:
        print("ERROR: PINECONE_API_KEY not set", file=sys.stderr)
        return 1

    os.environ["EMBEDDER_BACKEND"] = args.backend
    if args.dim:
        os.environ["GEMINI_EMBED_DIM"] = str(args.dim)

    embedder = create_embedder()
    dim = args.dim or getattr(embedder, "embed_dim", None) or _default_dim()

    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index_name = args.index or os.getenv("PINECONE_INDEX_NAME", "visionffe-gemini-test")
    index = ensure_index(pc, index_name, dim)
    namespace = args.namespace or os.getenv("PINECONE_NAMESPACE", "__default__")

    if args.source == "csv":
        rows = iter_csv(args.path or os.path.join(_BACKEND_DIR, "..", "data", "efreshli-products.csv"))
    elif args.source == "folder":
        rows = iter_folder(args.path)
    elif args.source == "urls":
        rows = iter_urls(args.path)
    else:
        print(f"ERROR: unknown source {args.source}", file=sys.stderr)
        return 1

    batch: List[Dict[str, Any]] = []
    ok = 0
    failed = 0
    processed = 0

    def flush():
        if batch:
            index.upsert(vectors=batch, namespace=namespace)
            batch.clear()

    for row in rows:
        if args.limit and processed >= args.limit:
            break
        processed += 1
        vec = _embed_row(embedder, row)
        if vec is None:
            failed += 1
            continue

        vector_id = row.get("id") or uuid.uuid4().hex
        meta = enrich_pinecone_metadata(row.get("metadata") or {})
        batch.append({"id": str(vector_id), "values": vec.tolist(), "metadata": meta})
        ok += 1

        if len(batch) >= args.batch_size:
            flush()
            print(f"  upserted {ok} (failed {failed})...")

    flush()

    stats = index.describe_index_stats()
    print(json.dumps({
        "backend": args.backend,
        "model": getattr(embedder, "model_key", None),
        "index": index_name,
        "namespace": namespace,
        "dimension": dim,
        "embedded": ok,
        "failed": failed,
        "index_total_vectors": stats.get("total_vector_count", 0),
    }, indent=2))
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="VisionFFE embedding ingest tool")
    p.add_argument("--backend", default=os.getenv("EMBEDDER_BACKEND", "gemini"),
                   choices=["gemini", "openclip"])
    p.add_argument("--source", default="csv", choices=["csv", "folder", "urls"])
    p.add_argument("--path", default=None, help="CSV/URLs file or image folder path")
    p.add_argument("--index", default=None, help="Pinecone index name (created if missing)")
    p.add_argument("--namespace", default=None)
    p.add_argument("--dim", type=int, default=None, help="Embedding + index dimension")
    p.add_argument("--limit", type=int, default=0, help="Max items to ingest (0 = all)")
    p.add_argument("--batch-size", type=int, default=50)
    args = p.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
