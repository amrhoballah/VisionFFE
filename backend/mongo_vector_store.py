"""
MongoDB Atlas Vector Search adapter.

Exposes a small Pinecone-index-shaped surface (upsert / query / describe_index_stats)
backed by a MongoDB collection + Atlas `$vectorSearch` aggregation stage, so the rest
of the app (retrieval.py, image_uploader.py, ingest/eval scripts) only needed to swap
which client builds `vector_index` rather than rewrite every call site.

Requires a MongoDB Atlas cluster (Vector Search indexes are an Atlas-only feature);
a local/self-hosted mongod cannot serve `$vectorSearch` queries.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import certifi
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.operations import SearchIndexModel

from auth_config import auth_settings

DEFAULT_NAMESPACE = "__default__"

_client: Optional[MongoClient] = None


def _get_client() -> MongoClient:
    """Lazily create a shared sync MongoClient for vector operations."""
    global _client
    if _client is None:
        is_atlas = "mongodb+srv://" in auth_settings.mongodb_url
        kwargs: Dict[str, Any] = {
            "serverSelectionTimeoutMS": 10000,
            "connectTimeoutMS": 10000,
        }
        if is_atlas:
            kwargs.update({"tls": True, "tlsCAFile": certifi.where()})
        _client = MongoClient(auth_settings.mongodb_url, **kwargs)
    return _client


def get_vector_collection(collection_name: Optional[str] = None) -> Collection:
    """Return the collection used to store embedding documents."""
    name = collection_name or os.getenv("MONGODB_VECTOR_COLLECTION", "embeddings")
    return _get_client()[auth_settings.mongodb_database][name]


class MongoVectorIndex:
    """Wraps a MongoDB Atlas collection + its `$vectorSearch` index."""

    def __init__(self, collection: Collection, index_name: str, dimension: int):
        self.collection = collection
        self.index_name = index_name
        self.dimension = dimension

    def upsert(self, vectors: List[Dict[str, Any]], namespace: str = DEFAULT_NAMESPACE) -> Dict[str, Any]:
        for v in vectors:
            self.collection.replace_one(
                {"_id": str(v["id"])},
                {
                    "_id": str(v["id"]),
                    "values": v["values"],
                    "metadata": v.get("metadata") or {},
                    "namespace": namespace,
                },
                upsert=True,
            )
        return {"upserted_count": len(vectors)}

    def query(
        self,
        vector: List[float],
        top_k: int = 10,
        include_metadata: bool = True,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> Dict[str, Any]:
        mongo_filter: Dict[str, Any] = {"namespace": {"$eq": namespace}}
        if filter:
            mongo_filter.update(filter)

        num_candidates = min(max(top_k * 10, 100), 10000)
        pipeline = [
            {
                "$vectorSearch": {
                    "index": self.index_name,
                    "path": "values",
                    "queryVector": vector,
                    "numCandidates": num_candidates,
                    "limit": top_k,
                    "filter": mongo_filter,
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        docs = self.collection.aggregate(pipeline)
        matches = [
            {
                "id": d["_id"],
                "score": d.get("score", 0.0),
                "metadata": (d.get("metadata") or {}) if include_metadata else {},
            }
            for d in docs
        ]
        return {"matches": matches}

    def describe_index_stats(self) -> Dict[str, Any]:
        return {
            "total_vector_count": self.collection.count_documents({}),
            "dimension": self.dimension,
            "index_fullness": 0,
        }


def ensure_vector_index(
    collection: Collection,
    index_name: str,
    dimension: int,
    similarity: str = "cosine",
    filter_fields: Optional[List[str]] = None,
    wait: bool = True,
) -> None:
    """Create the Atlas Vector Search index if it doesn't already exist (idempotent)."""
    db = collection.database
    if collection.name not in db.list_collection_names():
        # createSearchIndexes requires the collection to already exist.
        db.create_collection(collection.name)

    existing = {idx["name"] for idx in collection.list_search_indexes()}
    if index_name in existing:
        return

    fields: List[Dict[str, Any]] = [
        {"type": "vector", "path": "values", "numDimensions": dimension, "similarity": similarity},
        {"type": "filter", "path": "namespace"},
    ]
    for f in filter_fields or []:
        fields.append({"type": "filter", "path": f})

    model = SearchIndexModel(definition={"fields": fields}, name=index_name, type="vectorSearch")
    print(f"Creating MongoDB Atlas Vector Search index '{index_name}' (dim={dimension}, metric={similarity})...")
    collection.create_search_indexes([model])

    if not wait:
        return
    for _ in range(60):
        idx = next(iter(collection.list_search_indexes(index_name)), None)
        if idx and idx.get("queryable"):
            return
        time.sleep(2)
