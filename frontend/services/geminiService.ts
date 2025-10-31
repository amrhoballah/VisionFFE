import { GoogleGenAI, Type, Modality, Part } from "@google/genai";

const API_KEY = process.env.GEMINI_API_KEY || process.env.API_KEY;

if (!API_KEY) {
  throw new Error("GEMINI_API_KEY or API_KEY environment variable is not set");
}

const ai = new GoogleGenAI({ apiKey: API_KEY });

interface ImageInput {
  base64: string;
  mimeType: string;
}

const fileToGenerativePart = (base64: string, mimeType: string): Part => {
  return {
    inlineData: {
      data: base64,
      mimeType,
    },
  };
};

export async function identifyItems(
  images: ImageInput[]
): Promise<string[]> {
  try {
    const imageParts = images.map(img => fileToGenerativePart(img.base64, img.mimeType));
    
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: {
        parts: [
          ...imageParts,
          {
            text: "Analyze the provided room images, which show different angles of the same room. Identify every distinct piece of furniture, decor, and lighting. Consolidate items seen from multiple angles to avoid duplicates and use colours to differentiate between items. Provide a short, unique, descriptive name for each item. Return the result as a JSON array of strings. If the item is two of something just extract one of it",
          },
        ],
      },
      config: {
        temperature: 0.3,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.STRING,
            description: "A descriptive name for a single furniture or decor item.",
          },
        },
      },
    });

    const jsonText = response.text.trim();
    const items = JSON.parse(jsonText);
    return Array.isArray(items) ? items : [];

  } catch (error) {
    console.error("Error identifying items:", error);
    throw new Error("Failed to identify items from the images. Please try different ones.");
  }
}

export async function extractItemImage(
  images: ImageInput[],
  itemName: string
): Promise<string> {
    try {
        const imageParts = images.map(img => fileToGenerativePart(img.base64, img.mimeType));
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash-image",
            contents: {
                parts: [
                    ...imageParts,
                    { text: `From the provided images, find the best view of the '${itemName}' and create a new image that contains only that item. The item should be perfectly isolated with a transparent background and preferably be a frond view of the item.` },
                ],
            },
            config: {
                temperature: 0.5,
                responseModalities: [Modality.IMAGE],
            },
        });

        for (const part of response.candidates[0].content.parts) {
            if (part.inlineData && part.inlineData.mimeType.startsWith('image/')) {
                return part.inlineData.data;
            }
        }
        
        throw new Error("No image was extracted for this item.");
    } catch (error) {
        console.error(`Error extracting item "${itemName}":`, error);
        throw new Error(`Failed to extract "${itemName}".`);
    }
}
