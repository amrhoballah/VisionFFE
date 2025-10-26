"""
Gemini AI Service for furniture extraction and identification.
Handles image analysis using Google's Gemini AI models.
"""

import os
import json
from typing import List
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class ImageInput(BaseModel):
    base64: str
    mimeType: str

class ItemIdentificationResponse(BaseModel):
    items: List[str]

class ItemExtractionResponse(BaseModel):
    base64_image: str

class GeminiService:
    """Service for interacting with Google's Gemini AI models."""
    
    def __init__(self):
        """Initialize the Gemini service with API key from environment."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        self.client = genai.Client(api_key=api_key)
    
    def _file_to_generative_part(self, base64: str, mime_type: str) -> dict:
        """Convert base64 image to generative part format."""
        return {
            "inline_data": {
                "data": base64,
                "mime_type": mime_type,
            }
        }
    
    async def identify_items(self, images: List[ImageInput]) -> List[str]:
        """
        Analyze room images and identify all furniture/decor items.
        
        Args:
            images: List of base64-encoded images with mime types
            
        Returns:
            List of identified item names
        """
        try:
            # Convert images to generative parts
            image_parts = [
                self._file_to_generative_part(img.base64, img.mimeType) 
                for img in images
            ]
            
            # Prepare the request
            prompt = (
                "Analyze the provided room images, which show different angles of the same room. "
                "Identify every distinct piece of furniture, decor, and lighting. "
                "Consolidate items seen from multiple angles to avoid duplicates. "
                "Provide a short, unique, descriptive name for each item. "
                "Return the result as a JSON array of strings."
            )
            
            # Call Gemini API
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents={
                    "parts": [
                        *image_parts,
                        {"text": prompt}
                    ]
                },
                config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "A descriptive name for a single furniture or decor item.",
                        },
                    },
                },
            )
            
            # Parse and return results
            json_text = response.text.strip()
            items = json.loads(json_text)
            return items if isinstance(items, list) else []
            
        except Exception as error:
            print(f"Error identifying items: {error}")
            raise ValueError("Failed to identify items from the images. Please try different ones.")
    
    async def extract_item_image(self, images: List[ImageInput], item_name: str) -> str:
        """
        Extract a specific item from room images as an isolated image.
        
        Args:
            images: List of base64-encoded images with mime types
            item_name: Name of the item to extract
            
        Returns:
            Base64-encoded image of the extracted item
        """
        try:
            # Convert images to generative parts
            image_parts = [
                self._file_to_generative_part(img.base64, img.mimeType) 
                for img in images
            ]
            
            # Prepare the request
            prompt = (
                f"From the provided images, find the best view of the '{item_name}' "
                "and create a new image that contains only that item. "
                "The item should be perfectly isolated with a transparent background."
            )
            
            # Call Gemini API
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents={
                    "parts": [
                        *image_parts,
                        {"text": prompt}
                    ]
                },
                config={
                    "response_modalities": ["image"],
                },
            )
            
            # Extract the image from response
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith('image/'):
                    return part.inline_data.data
            
            raise ValueError("No image was extracted for this item.")
            
        except Exception as error:
            print(f"Error extracting item '{item_name}': {error}")
            raise ValueError(f"Failed to extract '{item_name}'.")


# Create singleton instance
_gemini_service = None

def get_gemini_service() -> GeminiService:
    """Get or create the Gemini service singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service

