// Backend Gemini Service - Frontend service for calling backend Gemini API
import { authService } from './authService';
import config from '../config';

export interface ImageInput {
  base64: string;
  mimeType: string;
}

interface IdentifyItemsRequest {
  images: ImageInput[];
}

interface IdentifyItemsResponse {
  items: string[];
}

interface ExtractItemRequest {
  images: ImageInput[];
  item_name: string;
}

interface ExtractItemResponse {
  base64_image: string;
}

class BackendGeminiService {
  private baseUrl: string;

  constructor(baseUrl: string = config.api.baseUrl) {
    this.baseUrl = baseUrl;
  }

  async identifyItems(images: ImageInput[]): Promise<string[]> {
    /**
     * Analyze room images and identify all furniture/decor items.
     * 
     * @param images List of images with base64 data and mime types
     * @returns List of identified item names
     */
    try {
      const request: IdentifyItemsRequest = { images };
      
      const response = await authService.authenticatedFetch(
        `${this.baseUrl}/api/gemini/identify`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred.' }));
        throw new Error(errorData.detail || 'Failed to identify items');
      }

      const data: IdentifyItemsResponse = await response.json();
      return data.items;

    } catch (error) {
      console.error('Error identifying items:', error);
      throw new Error('Failed to identify items from the images. Please try different ones.');
    }
  }

  async extractItemImage(images: ImageInput[], itemName: string): Promise<string> {
    /**
     * Extract a specific item from room images as an isolated image.
     * 
     * @param images List of images with base64 data and mime types
     * @param itemName Name of the item to extract
     * @returns Base64-encoded image of the extracted item
     */
    try {
      const request: ExtractItemRequest = { images, item_name: itemName };
      
      const response = await authService.authenticatedFetch(
        `${this.baseUrl}/api/gemini/extract`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred.' }));
        throw new Error(errorData.detail || 'Failed to extract item');
      }

      const data: ExtractItemResponse = await response.json();
      return data.base64_image;

    } catch (error) {
      console.error(`Error extracting item "${itemName}":`, error);
      throw new Error(`Failed to extract "${itemName}".`);
    }
  }
}

// Create and export a singleton instance
export const backendGeminiService = new BackendGeminiService();

// Export functions for backward compatibility
export async function identifyItems(images: ImageInput[]): Promise<string[]> {
  return backendGeminiService.identifyItems(images);
}

export async function extractItemImage(images: ImageInput[], itemName: string): Promise<string> {
  return backendGeminiService.extractItemImage(images, itemName);
}

