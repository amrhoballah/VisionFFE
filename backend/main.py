from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import torch
from contextlib import asynccontextmanager
import os
import json
from pinecone import Pinecone
from dotenv import load_dotenv
from image_embedder import ImageEmbedder
from image_embedder2 import ImageEmbedder2
from image_embedder3 import ImageEmbedder3
from image_uploader import ImageUploader
import boto3

# Authentication imports
from database import init_database, init_default_data, close_database
from auth_routes import router as auth_router
from admin_routes import router as admin_router
from projects_routes import router as projects_router
# from gemini_routes import router as gemini_router
from auth_dependencies import require_search_permission, require_upload_permission, require_stats_permission


load_dotenv()

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

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
    print("🔧 Initializing embedder model...")
    try:
        model_preset = os.getenv("MODEL_PRESET", "balanced")
        app.state.embedder = ImageEmbedder2(preset=model_preset, device=device)
        print(f"✅ Embedder loaded with preset: {model_preset}")
    except Exception as e:
        print(f"⚠️ Warning: Could not load embedder: {e}")
        print("   App will work but image search/upload may fail")

    # --- Initialize Pinecone ---
    print("🔍 Initializing Pinecone...")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "default")
    
    if not pinecone_api_key:
        print("⚠️ WARNING: PINECONE_API_KEY not found!")
    else:
        try:
            pc = Pinecone(api_key=pinecone_api_key)
            
            # Check if index exists
            if pinecone_index_name not in pc.list_indexes().names():
                print(f"⚠️ Warning: Index '{pinecone_index_name}' does not exist in Pinecone")
            else:
                app.state.pinecone = pc
                app.state.pinecone_index = pc.Index(pinecone_index_name)
                stats = app.state.pinecone_index.describe_index_stats()
                print(f"✅ Connected to Pinecone. Vectors: {stats['total_vector_count']}")
        except Exception as e:
            print(f"⚠️ Error initializing Pinecone: {e}")

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
            
            # Only create uploader if we have embedder and pinecone_index
            if app.state.embedder and app.state.pinecone_index:
                app.state.uploader = ImageUploader(
                    app.state.r2, 
                    app.state.r2_bucket, 
                    app.state.embedder, 
                    app.state.pinecone_index
                )
                print("✅ Connected to Cloudflare R2 and created uploader")
            else:
                print("⚠️ Skipping uploader creation: missing embedder or Pinecone")
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
# app.include_router(gemini_router)

@app.get("/")
async def root(request: Request):
    stats = None
    embedder = request.app.state.embedder
    pinecone_index = request.app.state.pinecone_index
    if pinecone_index:
        try:
            stats = pinecone_index.describe_index_stats()
        except:
            pass
    
    return {
        "status": "online",
        "model": "loaded" if embedder else "not loaded",
        "pinecone": "connected" if pinecone_index else "not connected",
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
    pinecone_index = request.app.state.pinecone_index
    
    if uploader is None:
        raise HTTPException(status_code=500, detail="Uploader service not available")
    if pinecone_index is None:
        raise HTTPException(status_code=500, detail="Pinecone not connected")
    
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
        
        stats = pinecone_index.describe_index_stats()
        
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
    pinecone_index = request.app.state.pinecone_index
    if pinecone_index is None:
        raise HTTPException(status_code=500, detail="Pinecone not connected")
    
    try:
        stats = pinecone_index.describe_index_stats()
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