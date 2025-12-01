from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status, Form
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import requests
import base64 as b64
import json
from pydantic import BaseModel

from models import Project, User
from schemas import ProjectCreate, ProjectResponse
from auth_dependencies import require_role_or_admin, require_search_permission
from gemini_service import get_gemini_service

router = APIRouter(prefix="/projects", tags=["projects"])

class DeletePhotoRequest(BaseModel):
    photo_url: str

def project_to_dict(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        user_id=str(project.user_id),
        photo_urls=project.photo_urls,
        extracted_items=project.extracted_items,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(current_user: User = Depends(require_role_or_admin("designer"))):
    projects = await Project.find(Project.user_id == current_user.id).to_list()
    return [project_to_dict(p) for p in projects]

@router.post("/", response_model=ProjectResponse)
async def create_project(data: ProjectCreate, current_user: User = Depends(require_role_or_admin("designer"))):
    # Optional: enforce unique name per user
    existing = await Project.find_one(Project.user_id == current_user.id, Project.name == data.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project name already exists")
    project = Project(name=data.name, user_id=current_user.id)
    await project.insert()
    return project_to_dict(project)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: User = Depends(require_role_or_admin("designer"))):
    try:
        project = await Project.find_one(Project.id == ObjectId(project_id), Project.user_id == current_user.id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project id")
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project_to_dict(project)

@router.post("/{project_id}/photos", response_model=ProjectResponse)
async def upload_project_photos(
    request: Request,
    project_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_role_or_admin("designer"))
):
    try:
        project = await Project.find_one(Project.id == ObjectId(project_id), Project.user_id == current_user.id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project id")
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


    uploader = request.app.state.uploader
    if uploader is None:
        raise HTTPException(status_code=500, detail="Uploader service not available")
    
    uploaded_urls: List[str] = []
    for file in files:
        file_url = await uploader.upload_image(file, f"projects/{project_id}")
        if file_url:
            uploaded_urls.append(file_url)

    project.photo_urls.extend(uploaded_urls)
    project.updated_at = datetime.utcnow()
    await project.save()
    return project_to_dict(project)

@router.delete("/{project_id}/photos", response_model=ProjectResponse)
async def delete_project_photo(
    request: Request,
    project_id: str,
    data: DeletePhotoRequest,
    current_user: User = Depends(require_role_or_admin("designer"))
):
    """Delete a photo URL from the project's photo_urls list and from R2 storage."""
    try:
        project = await Project.find_one(Project.id == ObjectId(project_id), Project.user_id == current_user.id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project id")
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Remove the photo URL from the list if it exists
    if data.photo_url in project.photo_urls:
        # Delete from R2 storage first
        uploader = request.app.state.uploader
        if uploader:
            try:
                await uploader.delete_image(data.photo_url)
            except Exception as r2_error:
                # Log error but continue with DB deletion
                print(f"Warning: Failed to delete from R2 storage: {r2_error}")
        
        # Remove from database
        project.photo_urls.remove(data.photo_url)
        project.updated_at = datetime.utcnow()
        await project.save()
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found in project")
    
    return project_to_dict(project)

@router.post("/{project_id}/identify")
async def identify_project_items(
    request: Request,
    project_id: str,
    files: Optional[List[UploadFile]] = File(None),
    urls: Optional[str] = Form(None),
    current_user: User = Depends(require_role_or_admin("designer")),
    gemini_service = Depends(get_gemini_service)
):
    """Identify furniture items from project photos (uploads files if provided, then identifies items using URLs)."""
    try:
        project = await Project.find_one(Project.id == ObjectId(project_id), Project.user_id == current_user.id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project id")
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    uploader = request.app.state.uploader
    if uploader is None:
        raise HTTPException(status_code=500, detail="Uploader service not available")
    
    # Collect all image URLs
    image_urls = []
    # If files are provided, upload them first and add URLs
    if files:
        uploaded_urls: List[str] = []
        for file in files:
            file_url = await uploader.upload_image(file, f"projects/{project_id}")
            if file_url:
                uploaded_urls.append(file_url)
                image_urls.append(file_url)
        
        # Update project with new photos
        if uploaded_urls:
            project.photo_urls.extend(uploaded_urls)
            project.updated_at = datetime.utcnow()
            await project.save()
    
    # Parse and add provided URLs
    if urls:
        try:
            url_list = json.loads(urls) if isinstance(urls, str) else urls
            image_urls.extend(url_list)
        except json.JSONDecodeError:
            # Single URL as string
            image_urls.append(urls)
    
    # Validate that we have at least one image
    if not image_urls:
        raise HTTPException(status_code=400, detail="No images provided. Either files or urls must be provided")
    
    # Call Gemini service to identify items
    try:
        items = await gemini_service.identify_items(image_urls)
        return {"items": items}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error identifying items: {e}")
        raise HTTPException(status_code=500, detail="Failed to identify items")

@router.post("/{project_id}/extract")
async def extract_project_items(
    request: Request,
    project_id: str,
    item_name: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    urls: Optional[str] = Form(None),
    current_user: User = Depends(require_role_or_admin("designer")),
    gemini_service = Depends(get_gemini_service)
):
    """Identify furniture items from project photos (uploads files if provided, then identifies items using URLs)."""
    try:
        project = await Project.find_one(Project.id == ObjectId(project_id), Project.user_id == current_user.id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project id")
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    

    # Collect all image URLs
    image_urls = project.photo_urls
    
    # Validate that we have at least one image
    if not image_urls:
        raise HTTPException(status_code=400, detail="No images provided. Either files or urls must be provided")
    
    # Call Gemini service to identify items
    try:
        images_base64 = []
        for img_url in image_urls:
            response = requests.get(img_url)
            response.raise_for_status()
            # Convert image bytes to base64
            img_base64 = b64.b64encode(response.content).decode('utf-8')
            mime_type = response.headers.get("Content-Type")
            images_base64.append({"base64": img_base64, "mimeType": mime_type})
        
        item_base64 = await gemini_service.extract_item_image(images_base64, item_name)

        
        uploader = request.app.state.uploader
        if uploader is None:
            raise HTTPException(status_code=500, detail="Uploader service not available")
        
        saved = []
        
        # Decode base64 string to bytes
        item_bytes = b64.b64decode(item_base64)
        
        uploaded_url = await uploader.upload_bytes(item_bytes, f"projects/{project_id}/extracted", filename="image.png")
        if uploaded_url:
            saved.append({"name": item_name, "url": uploaded_url})

        if saved:
            project.extracted_items.extend(saved)
            project.updated_at = datetime.utcnow()
            await project.save()

        return {"imageUrl": uploaded_url, "name": item_name} if uploaded_url else None

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error identifying items: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract item")


@router.post("/{project_id}/search")
async def search_similar(
    request: Request, 
    project_id: str,
    urls: Optional[str] = Form(None),
    top_k: int = Form(5),
    current_user = Depends(require_search_permission),
    gemini_service = Depends(get_gemini_service),
):
    try:
        project = await Project.find_one(Project.id == ObjectId(project_id), Project.user_id == current_user.id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project id")
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    embedder = request.app.state.embedder
    pinecone_index = request.app.state.pinecone_index
    
    if embedder is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    if pinecone_index is None:
        raise HTTPException(status_code=500, detail="Pinecone not connected")
    
    # Parse URLs if provided
    url_list = []
    if urls:
        try:
            url_list = json.loads(urls) if isinstance(urls, str) else urls
        except json.JSONDecodeError:
            url_list = [urls]  # Single URL as string
    
    # Validate that at least one input is provided
    if not url_list:
        raise HTTPException(status_code=400, detail="Urls must be provided")
    
    # Validate top_k
    if top_k < 1 or top_k > 100:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 100")
    
    try:
        all_results = []
        
        # Process URLs if provided
        if url_list:
            for url in url_list:
                # First, categorize the query image so we can restrict results
                try:
                    category = await gemini_service.categorize_item_from_url(url)
                except ValueError as e:
                    all_results.append({
                        "query_identifier": url,
                        "success": False,
                        "error": str(e),
                        "results": []
                    })
                    continue

                query_embedding = embedder.get_embedding(url)
                if query_embedding is None:
                    all_results.append({
                        "query_identifier": url,
                        "success": False,
                        "error": "Failed to process image from URL",
                        "results": []
                    })
                    continue
                
                # For Embedder 3
                results = pinecone_index.query(
                    vector=query_embedding.tolist(),
                    top_k=top_k,
                    include_metadata=True,
                    filter={"category": category},
                )

                # For Embedder 2
                # results = pinecone_index.search(
                #     namespace="__default__", 
                #     query={
                #         "inputs": {"text": query_embedding}, 
                #         "top_k": top_k
                #     }
                # )

                formatted_results = []
                # For Embedder 3
                for match in results['matches']:
                    result = {
                        "id": match['id'],
                        "similarity_score": float(match['score']),
                        "metadata": match.get('metadata', {}),
                        "image_path": match['metadata'].get('image_path', ''),
                        "filename": match['metadata'].get('filename', '')
                    }
                    formatted_results.append(result)

                # For Embedder 2
                # for match in results['result'].get('hits', []):
                #     result = {
                #         "id": match['_id'],
                #         "similarity_score": float(match['_score']),
                #         "metadata": match.get('fields', {}),
                #         "image_path": match['fields'].get('image_path', ''),
                #         "filename": match['fields'].get('filename', '')
                #     }
                #     formatted_results.append(result)
                
                all_results.append({
                    "query_identifier": url,
                    "success": True,
                    "results": formatted_results
                })
        
        total_queries = len(url_list)
        
        return {
            "success": True,
            "total_queries": total_queries,
            "results": all_results,
            "total_database_size": pinecone_index.describe_index_stats()['total_vector_count']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

