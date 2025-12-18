# VisionFFE

## Architecture & High-Level Flow

VisionFFE is an AI-powered furniture extraction and search system built with a **FastAPI + MongoDB** backend and a **React + TypeScript** frontend. At a high level:

- **Backend (Python)**
  - **Framework**: `FastAPI` with async startup/shutdown using a `lifespan` context.
  - **Database & ODM**: MongoDB with **Beanie** documents:
    - `User`, `Role`, `Permission`, `Token`, `Project`.
  - **Auth & Roles**: Custom auth + admin routes with role/permission-based guards (e.g. `require_upload_permission`, `require_stats_permission`).
  - **Vector Search**: **Pinecone** for storing image embeddings and running similarity search.
  - **Storage**: **Cloudflare R2** (S3-compatible via `boto3`) for original and processed images.
  - **Embeddings / ML**: PyTorch + `ImageEmbedder3` to turn images into vectors for search.
  - **AI Models (Gemini)**: Google **Gemini** via `google.genai` in `gemini_service.py`:
    - `identify_items` → takes room images and returns a JSON list of identified furniture/decor items.
    - `extract_item_image` → generates an isolated cut-out image (base64) for a chosen item.
    - `categorize_item_from_url` → classifies a single item image into a constrained set of categories (e.g. Sofas, Dining Chairs, Side Tables, Coffee Tables, Arm Chairs).

- **Frontend (React + TS, Vite)**
  - **Framework & Tooling**: React + TypeScript, built with Vite.
  - **State/Auth**: `AuthContext` manages login state and user roles, providing route-level gating in `App.tsx`.
  - **Main Screens**: `HomePage`, `LoginPage`, `RegistrationPage`, `ProjectsPage`, and `ExtractorApp`.
  - **API Layer**:
    - `authService` for login/registration and attaching tokens.
    - `projectService` for user projects and their photos/items.
    - `backendGeminiService` for calling backend Gemini endpoints (`/api/gemini/identify`, `/api/gemini/extract`).

### End-to-End User Flow

1. **Authentication & Access**
   - User registers/logs in from the React app.
   - Frontend talks to FastAPI auth routes, receives access/refresh tokens, and `AuthContext` keeps the session.
   - Only users with roles like **designer**/**admin** can access the main `ExtractorApp`.

2. **Project Creation & Image Upload**
   - In `ProjectsPage` / `ExtractorApp`, the user creates or selects a project.
   - User uploads room renders; frontend sends them to `/api/upload`.
   - Backend stores images in **Cloudflare R2**, embeds them with `ImageEmbedder3`, and upserts vectors into **Pinecone**.

3. **Furniture/Decor Identification (Gemini)**
   - Frontend calls `backendGeminiService.identifyItems(images)` which hits the FastAPI Gemini route.
   - `GeminiService.identify_items` calls Gemini 2.5 Flash and returns a JSON list of item names (with subcategories).
   - Frontend displays the identified items for user selection.

4. **Item Extraction (Gemini)**
   - User selects an item; frontend calls `extractItemImage(images, itemName)`.
   - `GeminiService.extract_item_image` uses Gemini 2.5 Flash Image to generate an isolated, transparent-background image of that item, returned as base64.
   - Frontend shows the cut-out and can store it in the project’s `extracted_items`.

5. **Categorization & Search**
   - For single-item images, backend can call `categorize_item_from_url` to assign a category from the fixed list.
   - Combined with Pinecone embeddings, this enables category-aware similarity search across stored items.

6. **Admin & Stats**
   - Admin routes manage users, roles, and permissions.
   - `/api/database/stats` exposes vector index statistics (total vectors, dimensions, device, etc.), protected by `require_stats_permission`.

This pipeline ties together **React + TS frontend → FastAPI backend → MongoDB/Beanie → Cloudflare R2 → ImageEmbedder + Pinecone → Gemini** to deliver furniture discovery and extraction from multi-angle room images.
