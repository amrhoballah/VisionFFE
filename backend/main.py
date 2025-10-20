from fastapi import FastAPI, File, UploadFile, HTTPException, Request
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


load_dotenv()

app = FastAPI(
    title="VisionFFE API",
    description="AI-powered furniture image similarity search using deep learning",
    version="0.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events cleanly."""
    print("🚀 Starting up...")

    # --- Initialize Embedder ---
    model_preset = os.getenv("MODEL_PRESET", "newest")
    app.state.embedder = ImageEmbedder3(preset=model_preset, device=device)
    

    # --- Initialize Pinecone ---
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pincone_index_name = os.getenv("PINECONE_INDEX_NAME","default")
    if not pinecone_api_key:
        print("⚠️ WARNING: PINECONE_API_KEY not found!")
        yield
        return

    try:
        pc = Pinecone(api_key=pinecone_api_key)

        # Create Pinecone index if missing
        if pincone_index_name not in pc.list_indexes().names():
            print(f"❌ Error initializing Pinecone: Index '{pincone_index_name}' does not exist.")

        app.state.pinecone = pc
        app.state.pinecone_index = pc.Index(pincone_index_name)

        stats = app.state.pinecone_index.describe_index_stats()
        print(f"✅ Connected to Pinecone. Vectors: {stats['total_vector_count']}")

    except Exception as e:
        print(f"❌ Error initializing Pinecone: {e}")


    try:
        r2_client = boto3.client(
            "s3",
            endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            region_name=os.getenv("R2_REGION", "auto"),
        )
        app.state.r2 = r2_client
        app.state.r2_bucket = os.getenv("R2_BUCKET_NAME")
        app.state.uploader = ImageUploader(app.state.r2, app.state.r2_bucket, app.state.embedder, app.state.pinecone_index)
        print("✅ Connected to Cloudflare R2")
    except Exception as e:
        print(f"⚠️ Error connecting to R2: {e}")
    # --- Let the app run ---
    yield

app = FastAPI(lifespan=lifespan)

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

@app.post("/api/search")
async def search_similar(request: Request, file: UploadFile = File(...), top_k: int = 5):
    embedder = request.app.state.embedder
    pinecone_index = request.app.state.pinecone_index
    if embedder is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    if pinecone_index is None:
        raise HTTPException(status_code=500, detail="Pinecone not connected")
    
    try:
        query_embedding = await request.app.state.uploader.search_item(file)

        if query_embedding is None:
            raise HTTPException(status_code=400, detail="Failed to process image")
        
        results = pinecone_index.query(
            vector=query_embedding.tolist(),
            top_k=top_k,
            include_metadata=True
        )
        
        formatted_results = []
        for match in results['matches']:
            result = {
                "id": match['id'],
                "similarity_score": float(match['score']),
                "metadata": match.get('metadata', {}),
                "image_path": match['metadata'].get('image_path', ''),
                "filename": match['metadata'].get('filename', '')
            }
            formatted_results.append(result)
        
        return {
            "success": True,
            "query_filename": file.filename,
            "results": formatted_results,
            "total_database_size": pinecone_index.describe_index_stats()['total_vector_count']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/upload")
async def upload_images(request: Request, files: List[UploadFile] = File(...), metadata: Optional[str] = None):
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
            success = await request.app.state.uploader.add_furniture_item(file, file_metadata)
            if success:
                vectors_to_upsert.append(file.filename)
        
        stats = app.state.pinecone_index.describe_index_stats()
        
        return {
            "success": True,
            "uploaded": len(vectors_to_upsert),
            "failed": len(files) - len(vectors_to_upsert),
            "total_database_size": stats['total_vector_count']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/database/stats")
async def get_database_stats(request: Request):
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