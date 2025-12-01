export interface SearchResult {
  id: string;
  similarity_score: number;
  metadata: Record<string, any>;
  image_path: string;
  filename: string;
}

export interface ExtractedItem {
  id: string;
  name: string;
  imageBase64: string;
  imageUrl?: string; // URL from backend when loading existing items
  searchResults?: SearchResult[];
}
