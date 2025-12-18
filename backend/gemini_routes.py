"""
API routes for Gemini AI service endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import base64
import json

from gemini_service import get_gemini_service, GeminiService, ImageInput
from auth_dependencies import get_current_active_user, require_role_or_admin
from models import User

router = APIRouter(prefix="/api/gemini", tags=["gemini"])

class ImageInputRequest(BaseModel):
    base64: str
    mimeType: str

class IdentifyItemsRequest(BaseModel):
    images: List[ImageInputRequest]

class IdentifyItemsResponse(BaseModel):
    items: List[str]

class ItemCategoryResponse(BaseModel):
    category: str
class ExtractItemRequest(BaseModel):
    images: List[ImageInputRequest]
    item_name: str

class ExtractItemResponse(BaseModel):
    base64_image: str

@router.post("/identify", response_model=IdentifyItemsResponse)
async def identify_items(
    request: IdentifyItemsRequest,
    gemini_service: GeminiService = Depends(get_gemini_service),
    current_user: User = Depends(require_role_or_admin("designer"))
):
    """
    Analyze room images and identify all furniture/decor items.
    Requires authentication.
    """
    try:
        # Convert request to ImageInput objects
        images = [ImageInput(base64=img.base64, mimeType=img.mimeType) for img in request.images]
        
        # Call Gemini service
        items = await gemini_service.identify_items(images)
        
        return IdentifyItemsResponse(items=items)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in identify endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to identify items")

@router.post("/extract", response_model=ExtractItemResponse)
async def extract_item(
    request: ExtractItemRequest,
    gemini_service: GeminiService = Depends(get_gemini_service),
    current_user: User = Depends(require_role_or_admin("designer"))
):
    """
    Extract a specific item from room images as an isolated image.
    Requires authentication.
    """
    try:
        # Convert request to ImageInput objects
        images = [ImageInput(base64=img.base64, mimeType=img.mimeType) for img in request.images]
        
        # Call Gemini service
        base64_image = await gemini_service.extract_item_image(images, request.item_name)
        
        return ExtractItemResponse(base64_image=base64_image)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in extract endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract item")

