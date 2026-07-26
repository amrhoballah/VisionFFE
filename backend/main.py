from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from contextlib import asynccontextmanager
import os
import json
from dotenv import load_dotenv
from embedder_factory import create_embedder
from image_uploader import ImageUploader
from mongo_vector_store import MongoVectorIndex, ensure_vector_index, get_vector_collection
import boto3

# Authentication imports
from database import init_database, init_default_data, close_database
from auth_routes import router as auth_router
from admin_routes import router as admin_router
from projects_routes import router as projects_router
from embeddings_routes import router as embeddings_router
# from gemini_routes import router as gemini_router
from auth_dependencies import require_search_permission, require_upload_permission, require_stats_permission


load_dotenv()

# torch is only required by the OpenCLIP backend (EMBEDDER_BACKEND=openclip); the
# default Gemini backend needs no GPU, so keep the import optional here too.
try:
    import torch

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
except ImportError:
    device = "cpu"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events cleanly."""
    print("🚀 Starting up...")

    # --- Initialize MongoDB Database ---
    print("📊 Initializing MongoDB database...")
    try:
        await init_database()
        await init_default_data()
        print("✅ MongoDB database initialized")
    except Exception as e:
        print(f"❌ Error initializing MongoDB: {e}")
        yield
        return

    # --- Initialize Embedder ---
    # Backend selected via EMBEDDER_BACKEND (default "gemini" = Gemini Embedding 2, no GPU).
    # NOTE: switching backends changes the vector space AND dimension, so MONGODB_VECTOR_COLLECTION
    # must point at a collection that matches the active backend (re-embed the catalog per backend).
    print("🔧 Initializing embedder model...")
    app.state.embedder = None
    try:
        app.state.embedder = create_embedder(device=device)
        backend = os.getenv("EMBEDDER_BACKEND", "gemini")
        print(f"✅ Embedder loaded (backend: {backend})")
        if hasattr(app.state.embedder, "model_key"):
            print(f"   Resolved embedding profile: {app.state.embedder.model_key}")
    except Exception as e:
        print(f"⚠️ Warning: Could not load embedder: {e}")
        print("   App will work but image search/upload may fail")

    # --- Initialize MongoDB Atlas Vector Search ---
    print("🔍 Initializing MongoDB Atlas Vector Search...")
    app.state.vector_index = None
    try:
        collection_name = os.getenv("MONGODB_VECTOR_COLLECTION", "embeddings")
        search_index_name = os.getenv("VECTOR_SEARCH_INDEX_NAME", "vector_index")
        dim = int(os.getenv("GEMINI_EMBED_DIM", "1536"))

        collection = get_vector_collection(collection_name)
        ensure_vector_index(collection, search_index_name, dim, filter_fields=["search_family"])

        app.state.vector_index = MongoVectorIndex(collection, search_index_name, dim)
        stats = app.state.vector_index.describe_index_stats()
        print(f"✅ Connected to MongoDB Atlas Vector Search. Vectors: {stats['total_vector_count']}")
    except Exception as e:
        print(f"⚠️ Error initializing MongoDB Atlas Vector Search: {e}")

    # --- Initialize Cloudflare R2 ---
    print("☁️  Initializing Cloudflare R2...")
    try:
        r2_account_id = os.getenv("R2_ACCOUNT_ID")
        r2_access_key = os.getenv("R2_ACCESS_KEY_ID")
        r2_secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        
        if not all([r2_account_id, r2_access_key, r2_secret_key]):
            print("⚠️ Warning: R2 credentials incomplete")
        else:
            r2_client = boto3.client(
                "s3",
                endpoint_url=f"https://{r2_account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=r2_access_key,
                aws_secret_access_key=r2_secret_key,
                region_name=os.getenv("R2_REGION", "auto"),
            )
            app.state.r2 = r2_client
            app.state.r2_bucket = os.getenv("R2_BUCKET_NAME")
            
            # Only create uploader if we have embedder and vector_index
            if app.state.embedder and app.state.vector_index:
                app.state.uploader = ImageUploader(
                    app.state.r2,
                    app.state.r2_bucket,
                    app.state.embedder,
                    app.state.vector_index
                )
                print("✅ Connected to Cloudflare R2 and created uploader")
            else:
                print("⚠️ Skipping uploader creation: missing embedder or vector index")
    except Exception as e:
        print(f"⚠️ Error connecting to R2: {e}")
    
    # --- Let the app run ---
    print("✨ Application startup complete")
    yield
    
    # --- Cleanup on shutdown ---
    print("🛑 Shutting down...")
    await close_database()

app = FastAPI(
    title="VisionFFE API",
    description="AI-powered furniture image similarity search using deep learning",
    version="0.0.1",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(projects_router)
app.include_router(embeddings_router)
# app.include_router(gemini_router)

@app.get("/")
async def root(request: Request):
    stats = None
    embedder = request.app.state.embedder
    vector_index = request.app.state.vector_index
    if vector_index:
        try:
            stats = vector_index.describe_index_stats()
        except:
            pass

    return {
        "status": "online",
        "model": "loaded" if embedder else "not loaded",
        "vector_db": "connected" if vector_index else "not connected",
        "database_size": stats['total_vector_count'] if stats else 0,
        "device": str(device)
    }


@app.post("/api/upload")
async def upload_images(
    request: Request,
    files: List[UploadFile] = File(...),
    metadata: Optional[str] = None,
    current_user = Depends(require_upload_permission)
):
    uploader = request.app.state.uploader
    vector_index = request.app.state.vector_index

    if uploader is None:
        raise HTTPException(status_code=500, detail="Uploader service not available")
    if vector_index is None:
        raise HTTPException(status_code=500, detail="Vector database not connected")

    try:
        metadata_list = []
        if metadata:
            try:
                metadata_list = json.loads(metadata)
            except json.JSONDecodeError:
                pass

        vectors_to_upsert = []
        for i, file in enumerate(files):
            file_metadata = metadata_list[i] if i < len(metadata_list) else {}
            success = await uploader.add_furniture_item(file, file_metadata)
            if success:
                vectors_to_upsert.append(file.filename)

        stats = vector_index.describe_index_stats()

        return {
            "success": True,
            "uploaded": len(vectors_to_upsert),
            "failed": len(files) - len(vectors_to_upsert),
            "total_database_size": stats['total_vector_count']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/database/stats")
async def get_database_stats(
    request: Request,
    current_user = Depends(require_stats_permission)
):
    embedder = request.app.state.embedder
    vector_index = request.app.state.vector_index
    if vector_index is None:
        raise HTTPException(status_code=500, detail="Vector database not connected")

    try:
        stats = vector_index.describe_index_stats()
        return {
            "total_images": stats['total_vector_count'],
            "dimension": stats.get('dimension', 0),
            "index_fullness": stats.get('index_fullness', 0),
            "model_device": str(device)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)