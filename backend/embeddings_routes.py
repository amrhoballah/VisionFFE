"""
Ad-hoc embedding upload endpoint for testing the active embedding backend.

Lets an upload-permitted user POST one or more image files; each is uploaded to R2,
embedded with the currently configured embedder (Gemini Embedding 2 by default), and
upserted into the configured MongoDB Atlas Vector Search collection. Mirrors the
existing `/api/upload` behavior but lives under `/api/embeddings` for test-focused use.
"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from auth_dependencies import require_upload_permission

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])


@router.post("/upload")
async def upload_embeddings(
    request: Request,
    files: List[UploadFile] = File(...),
    metadata: Optional[str] = None,
    current_user=Depends(require_upload_permission),
):
    """Upload image(s), auto-embed with the active backend, and upsert to MongoDB Atlas Vector Search."""
    uploader = request.app.state.uploader
    vector_index = request.app.state.vector_index
    embedder = request.app.state.embedder

    if uploader is None:
        raise HTTPException(status_code=500, detail="Uploader service not available")
    if vector_index is None:
        raise HTTPException(status_code=500, detail="Vector database not connected")

    metadata_list = []
    if metadata:
        try:
            metadata_list = json.loads(metadata)
        except json.JSONDecodeError:
            metadata_list = []

    try:
        uploaded = []
        for i, file in enumerate(files):
            file_metadata = metadata_list[i] if i < len(metadata_list) else {}
            success = await uploader.add_furniture_item(file, file_metadata)
            if success:
                uploaded.append(file.filename)

        stats = vector_index.describe_index_stats()
        return {
            "success": True,
            "backend": getattr(embedder, "model_key", None),
            "uploaded": len(uploaded),
            "failed": len(files) - len(uploaded),
            "total_database_size": stats.get("total_vector_count", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding upload failed: {str(e)}")
