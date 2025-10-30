from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status
from typing import List
from bson import ObjectId
from datetime import datetime
import os
import uuid

from models import Project, User
from schemas import ProjectCreate, ProjectResponse
from auth_dependencies import get_current_active_user, require_role_or_admin

router = APIRouter(prefix="/projects", tags=["projects"])

def project_to_dict(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        user_id=str(project.user_id),
        photo_urls=project.photo_urls,
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

    r2_client = request.app.state.r2
    bucket = request.app.state.r2_bucket
    if not r2_client or not bucket:
        raise HTTPException(status_code=500, detail="Storage not configured")

    uploaded_urls: List[str] = []
    base_url = os.getenv("R2_URL")
    for file in files:
        file_bytes = await file.read()
        ext = os.path.splitext(file.filename)[1]
        key = f"projects/{project_id}/{uuid.uuid4().hex}{ext}"
        r2_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=file_bytes,
            ContentType=file.content_type
        )
        file_url = f"{base_url}/{key}" if base_url else key
        uploaded_urls.append(file_url)

    project.photo_urls.extend(uploaded_urls)
    project.updated_at = datetime.utcnow()
    await project.save()
    return project_to_dict(project)


