# Gemini Embedding 2 backend + embedding test tools

VisionFFE can now embed furniture images with **Gemini Embedding 2**
(`gemini-embedding-2-preview`), Google's natively multimodal embedding model, instead of the
local OpenCLIP model. It runs through the same `google-genai` SDK and `GEMINI_API_KEY` already
used by `gemini_service.py`, so no GPU and no extra Google Cloud setup are required.

## What changed

- `backend/gemini_embedder.py` — `GeminiImageEmbedder`, a drop-in replacement for `ImageEmbedder3`.
- `backend/embedder_factory.py` — `create_embedder()` picks the backend from `EMBEDDER_BACKEND`.
- `backend/main.py` — the app now builds its embedder via the factory (default: `gemini`).
- `backend/projects_routes.py` — search embeds the query with `task_type=RETRIEVAL_QUERY`.
- `backend/embeddings_routes.py` — `POST /api/embeddings/upload` ad-hoc upload + embed endpoint.
- `backend/scripts/ingest_embeddings.py` — bulk CSV/folder/URL ingest tool.
- `backend/scripts/eval_retrieval.py` — now takes `--backend gemini|openclip` for A/B comparison.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `EMBEDDER_BACKEND` | `gemini` | `gemini` or `openclip` |
| `GEMINI_API_KEY` | — | Gemini API key (already required by the app) |
| `GEMINI_EMBED_MODEL` | `gemini-embedding-2-preview` | Embedding model id |
| `GEMINI_EMBED_DIM` | `1536` | Output + Atlas Vector Search index dimension (Matryoshka, 128–3072) |
| `MONGODB_URL` | `mongodb://localhost:27017` | **Must** be an Atlas cluster — Vector Search is an Atlas-only feature |
| `MONGODB_VECTOR_COLLECTION` | `embeddings` | **Must** match the active backend's dimension |
| `VECTOR_SEARCH_INDEX_NAME` | `vector_index` | Atlas Vector Search index name on that collection |
| `VECTOR_NAMESPACE` | `__default__` | Namespace field for query/upsert |
| `MODEL_PRESET` | `balanced` | OpenCLIP preset (only when `EMBEDDER_BACKEND=openclip`) |

> **Important:** Gemini and OpenCLIP produce different vector spaces *and* dimensions, so each
> backend needs its **own** MongoDB collection. Point `MONGODB_VECTOR_COLLECTION` at the collection
> that matches the backend you're running.

## 1. Bulk ingest the catalog into a fresh Gemini collection

```bash
cd backend
export EMBEDDER_BACKEND=gemini GEMINI_EMBED_DIM=1536
python scripts/ingest_embeddings.py \
  --backend gemini --source csv \
  --path ../data/efreshli-products.csv \
  --limit 50 --collection visionffe_gemini_test
```

The script creates the `visionffe_gemini_test` collection and its Atlas Vector Search index
(dim 1536, cosine) if missing, embeds each product image, enriches metadata (`search_family`,
etc.), and upserts into MongoDB. Other sources: `--source folder --path ./imgs` (local files) or
`--source urls --path urls.txt`.

## 2. Ad-hoc single-image test via the API

```bash
curl -X POST http://localhost:8080/api/embeddings/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "files=@sofa.jpg" \
  -F 'metadata=[{"title":"Test Sofa","sub_category":"Sofas"}]'
```

Requires a user with upload permission. Returns `uploaded`/`failed` counts, the active `backend`,
and the collection's vector total.

## 3. Search against the Gemini collection

Point the running app at the Gemini collection (`EMBEDDER_BACKEND=gemini`,
`MONGODB_VECTOR_COLLECTION=visionffe_gemini_test`) and call `POST /projects/{id}/search` with an
item URL. Pass `search_debug=true` to confirm `embed_model` shows the Gemini model.

## 4. A/B quality comparison (Recall@K / MRR)

Run the same manifest through each backend (each against its matching collection):

```bash
cd backend
# Gemini
MONGODB_VECTOR_COLLECTION=visionffe_gemini_test \
  python scripts/eval_retrieval.py --backend gemini --manifest ../data/eval_manifest.example.json
# OpenCLIP (existing collection)
MONGODB_VECTOR_COLLECTION=<openclip-collection> \
  python scripts/eval_retrieval.py --backend openclip --manifest ../data/eval_manifest.example.json
```

Compare `recall_at_k_*` and `mrr_*` in the two JSON reports to decide whether Gemini improves
retrieval for the catalog. Once confirmed, `torch`/`open-clip-torch` can be dropped from
`requirements.txt` and the Modal deployment can drop its GPU.
