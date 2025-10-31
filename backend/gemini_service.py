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
from google.genai import types
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
    
    item_schema = {
        "type": types.Type.STRING,
        "description": "A descriptive name for a single furniture or decor item."
    }


    def __init__(self):
        """Initialize the Gemini service with API key from environment."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        self.client = genai.Client(api_key=api_key)
    
    def _file_to_generative_part(self, base64: str, mime_type: str):
        """Convert base64 image to generative part format."""
        return types.Part(
            inline_data= {
                "data": base64,
                "mime_type": mime_type
            }
        )
    
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
                mime_type = response.headers.get("Content-Type")
                images_base64.append({"base64": img_base64, "mimeType": mime_type})
            
            # Convert images to generative parts
            print("I am here 5")
            image_parts = [
                self._file_to_generative_part(img["base64"], img["mimeType"]) 
                for img in images_base64
            ]

            print("I am here 6")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "Analyze the provided room images, which show different angles of the same room. Identify every distinct piece of furniture, decor, and lighting. Consolidate items seen from multiple angles to avoid duplicates and use colours to differentiate between items. Provide a short, unique, descriptive name for each item. Return the result as a JSON array of strings. If the item is two of something just extract one of it",
                    *image_parts
                ],
                config= types.GenerateContentConfig(
                    temperature= 0.3,
                    response_mime_type= "application/json",
                    # response_schema=types.Schema(
                    #     type=types.Type.ARRAY,
                    #     items=types.Schema(
                    #         type=types.Type.STRING,
                    #         description="A descriptive name for a single furniture or decor item."
                    #     )
                    # )
                )
            )
            
            # Parse and return results
            json_text = response.text.strip()
            items = json.loads(json_text)
            return items if isinstance(items, list) else []
            
        except Exception as error:
            print(f"Error identifying items: {error}")
            raise ValueError("Failed to identify items from the images. Please try different ones.")


    def extract_item_image(images: List[ImageInput], item_name: str) -> str:
        """
        Extracts a specific item from room images into a new, isolated image.

        Args:
            images: A list of dictionaries with base64 image data and MIME types.
            item_name: The name of the item to extract.

        Returns:
            A base64-encoded PNG string of the extracted item image.
            
        Raises:
            Exception: If the API fails or no image is returned.
        """
        try:

            # Convert image inputs.
            image_parts = [_file_to_generative_part(img['base64'], img['mimeType']) for img in images]

            # The prompt to guide the image generation.
            prompt = (
                f"From the provided images, find the best view of the '{item_name}' "
                "and create a new image that contains only that item. The item should "
                "be perfectly isolated with a transparent background and preferably be a front view of the item."
            )

            response = self.client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[
                        prompt,
                        *image_parts
                    ],
                    config= types.GenerateContentConfig(
                        temperature= 0.3
                    )
                )
            
            # The response will contain image data in its 'parts'.
            for part in response.candidates[0].content.parts:
                if part.inline_data and 'image' in part.inline_data.mime_type:
                    # Convert the raw image bytes back to a base64 string for transport.
                    image_bytes = part.inline_data.data
                    base64_string = base64.b64encode(image_bytes).decode('utf-8')
                    return base64_string
            
            # If no image was found in the response parts.
            raise Exception("No image was extracted for this item.")

        except Exception as e:
            print(f"Error extracting item '{item_name}': {e}")
            raise Exception(f"Failed to extract '{item_name}'.")
