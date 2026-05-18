# Testing guide: furniture similarity search changes

This document walks through verifying taxonomy (`search_family`), retrieval (fallback, threshold, re-rank), uploads, embeddings, and the offline eval script.

## Prerequisites

- Backend dependencies installed (`pip install -r backend/requirements.txt`).
- Environment variables set (at least `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `GEMINI_API_KEY`, R2 vars if you test upload). Optional tuning: `SIMILARITY_THRESHOLD`, `RETRIEVAL_CANDIDATES_K`, `EMBEDDER_MULTI_CROP`, `PINECONE_NAMESPACE`.
- Pinecone index dimension must match the embedder output (e.g. after changing `MODEL_PRESET`, recreate the index or use a matching index).

---

## 1. Smoke-test the backend

1. Start the API (from `backend/`): `uvicorn main:app --host 0.0.0.0 --port 8080` (or your usual command).
2. Open `GET /` and confirm `"model": "loaded"` and Pinecone connected.
3. Check logs for: `Resolved OpenCLIP profile: ...` and no embedder startup errors.

**Pass criteria:** App starts; embedder and Pinecone initialize.

---

## 2. Taxonomy mapping (unit-level, no network)

From `backend/`:

```bash
python3 -c "
from taxonomy import map_subcategory_to_search_family, enrich_pinecone_metadata
assert map_subcategory_to_search_family('Sofas & Sectionals') == 'Sofas'
assert map_subcategory_to_search_family('End & Side Tables') == 'Side Tables'
assert map_subcategory_to_search_family('Accent & Arm Chairs') == 'Arm Chairs'
m = enrich_pinecone_metadata({'sub_category': 'Coffee Tables', 'title': 'Foo'})
assert m['search_family'] == 'Coffee Tables'
assert m['sub_category_raw'] == 'Coffee Tables'
print('taxonomy OK')
"
```

**Pass criteria:** Assertions succeed; `search_family` and `sub_category_raw` appear on enriched metadata.

---

## 3. Catalog upload and Pinecone metadata

1. Call `POST /api/upload` with auth as a user who has upload permission, attaching at least one furniture image and JSON `metadata` per file, for example:

   - `sub_category`: `Sofas & Sectionals` (retailer-style label).

2. In Pinecone console (or a small script), fetch one vector by id and inspect **metadata**.

**Pass criteria:**

- Vector id matches the filename segment from the R2 URL (UUID + extension).
- Metadata includes **`search_family`** (e.g. `Sofas`), **`sub_category_raw`**, and **`sub_category`**.
- No upload errors in server logs.

---

## 4. Project search (end-to-end)

1. Create a project and upload room photos; run identify/extract so you have a **cut-out image URL** (same flow as production).
2. Call `POST /projects/{project_id}/search` with `urls` as JSON array of that image URL and `top_k=5`.
3. Repeat with `search_debug=true` (form field).

**Pass criteria:**

- Non-empty `results` when the catalog has items in the same `search_family` as Gemini’s category.
- With `search_debug`, each successful row includes `search_debug.retrieval.stages` (exact_family → related_families → no_filter as needed), `gemini_family`, `similarity_threshold`, and `embed_model`.
- Scores are present on each hit; no hard-coded `0.6` behavior (threshold comes from `SIMILARITY_THRESHOLD`).

**Regression checks:**

- Temporarily set `SIMILARITY_THRESHOLD=-1` and confirm more hits can appear (weaker matches not dropped).
- Set `SIMILARITY_THRESHOLD=0.9` and confirm fewer or zero hits (cutoff is active).

---

## 5. Gemini alignment

1. Call categorize path indirectly via search, or add a temporary route if you have one; otherwise rely on `search_debug.gemini_family` from step 4.
2. Run **identify** on a room that clearly contains a sofa.

**Pass criteria:**

- `categorize_item_from_url` still returns one of: Sofas, Dining Chairs, Side Tables, Coffee Tables, Arm Chairs.
- Identify prompt vocabulary is consistent with the same family list (no obvious sofa omission in prompts—see `gemini_service.py` and `taxonomy.SEARCH_FAMILY_PROMPT_LIST`).

---

## 6. Offline eval script

1. Copy `data/eval_manifest.example.json` to a working manifest (e.g. `eval_manifest.json`).
2. Add at least one real `queries[]` entry: `image_url` (publicly fetchable), `relevant_ids` (Pinecone vector ids you know are correct), `search_family` (must match Gemini’s five labels for filtered run).
3. From `backend/`:

   ```bash
   python scripts/eval_retrieval.py --manifest ../eval_manifest.json --k 1,5,10
   ```

4. Optional: `python scripts/eval_retrieval.py --manifest ... --preset siglip --multi-crop`

**Pass criteria:**

- Script exits 0; JSON reports `num_evaluated` > 0 when queries are valid.
- `recall_at_k_filtered` vs `recall_at_k_unfiltered` and MRR fields look sensible (non-NaN; with empty `relevant_ids`, recall stays 0—use real ids to measure).

---

## 7. Embedding / multi-crop (optional)

1. Set `EMBEDDER_MULTI_CROP=true` in the environment and restart the API.
2. Run the same search as in step 4 twice (with / without multi-crop) and compare top ids and scores in `search_debug` (if enabled) or raw results.

**Pass criteria:** No crashes; results may shift slightly—document whether quality improves for your images.

---

## 8. Frontend (ExtractorApp)

1. Run the normal UI flow: extract item → **send to search**.
2. Confirm results still map to items (same response shape: `id`, `similarity_score`, `metadata`).

**Pass criteria:** UI shows similar items without errors; empty state still acceptable if catalog is empty or threshold is strict.

---

## 9. Re-index reminder (data migration)

If most vectors were indexed **before** `search_family` existed:

- Re-upload catalog items via `POST /api/upload` with correct `sub_category`, **or** run a one-off migration that `upsert`s the same ids with updated metadata.

**Pass criteria:** Majority of production vectors include `search_family` so the **exact** filter stage returns enough hits without always falling back to unfiltered search.

---

## Quick checklist

| Step | What you verify |
|------|------------------|
| Startup | Embedder + Pinecone OK |
| Taxonomy script | Mapping + enrich fields |
| Upload | Metadata has `search_family` |
| Search | Results + optional `search_debug` |
| Threshold env | `SIMILARITY_THRESHOLD` behavior |
| Eval script | Recall/MRR with real manifest |
| Multi-crop | Optional quality check |
| UI | Extract → search still works |
| Migration | Old index rows updated |

If something fails, capture: `MODEL_PRESET`, index dimension from `GET /api/database/stats`, one redacted `search_debug` payload, and a sample vector’s metadata from Pinecone.
