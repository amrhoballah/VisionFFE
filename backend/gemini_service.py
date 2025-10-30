"""
Gemini AI Service for furniture extraction and identification.
Handles image analysis using Google's Gemini AI models.
"""

import os
import json
import base64 as b64
import requests
from typing import List
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Singleton instance
_gemini_service_instance = None

def get_gemini_service() -> 'GeminiService':
    """Get or create singleton GeminiService instance."""
    global _gemini_service_instance
    if _gemini_service_instance is None:
        _gemini_service_instance = GeminiService()
    return _gemini_service_instance

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
    
    async def identify_items(self, image_url: List[str]) -> List[str]:
        """
        Analyze room images and identify all furniture/decor items.
        
        Args:
            image_url: List of image URLs
            
        Returns:
            List of identified item names
        """
        try:
            print("I am here 4")
            images_base64 = []
            for img_url in image_url:
                response = requests.get(img_url)
                response.raise_for_status()
                # Convert image bytes to base64
                img_base64 = b64.b64encode(response.content).decode('utf-8')
                images_base64.append(img_base64)
            
            # Convert images to generative parts
            print("I am here 5")
            image_parts = [
                self._file_to_generative_part(img, "image/jpeg") 
                for img in images_base64
            ]

            print("I am here 6")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents={
                    "parts": image_parts + [
                        {
                            "text": "Analyze the provided room images, which show different angles of the same room. Identify every distinct piece of furniture, decor, and lighting. Consolidate items seen from multiple angles to avoid duplicates and use colours to differentiate between items. Provide a short, unique, descriptive name for each item. Return the result as a JSON array of strings. If the item is two of something just extract one of it",
                        },
                    ],
                },
                config={
                    "temperature": 0.3,
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