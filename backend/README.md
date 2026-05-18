# VisionFFE API

AI-powered FFE extraction and furniture image similarity search using deep learning and Pinecone vector database.

## Features

- 🔍 Find similar furniture images using AI
- 🚀 Fast similarity search with Pinecone
- 🎯 Multiple model presets (accuracy vs speed)
- 📊 RESTful API with FastAPI
- ☁️ Easy deployment to Modal with GPU support

## Local Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_REGION=us-east-1
MODEL_PRESET=balanced
```

### 3. Run Locally

```bash
python main.py
```

API will be available at: http://localhost:8000

## Deploy to Modal

### 1. Install Modal

```bash
pip install modal
```

### 2. Setup Modal Account

```bash
modal token new
```

### 3. Add Pinecone Secret to Modal

```bash
modal secret create pinecone-secret \\
  PINECONE_API_KEY=your_pinecone_api_key_here \\
  PINECONE_REGION=us-east-1 \\
  MODEL_PRESET=balanced
```

### 4. Deploy

```bash
modal deploy modal_deploy.py
```

Your API will be live at: `https://your-username--furniture-search-api.modal.run`

## API Endpoints

### Health Check
```bash
GET /
```

### Upload Images to Database
```bash
POST /api/upload
Content-Type: multipart/form-data

files: [image1.jpg, image2.jpg, ...]
metadata: '{"name": "Modern Sofa", "category": "sofa"}'  # Optional
```

### Search Similar Images
```bash
POST /api/search?top_k=5
Content-Type: multipart/form-data

file: query_image.jpg
```

### Get Database Stats
```bash
GET /api/database/stats
```

### Clear Database
```bash
DELETE /api/database/clear
```

## Model presets (`MODEL_PRESET`)

`ImageEmbedder3` uses **OpenCLIP** only. Each preset resolves to a `MODEL::PRETRAINED` pair:

| Preset | OpenCLIP profile |
|--------|------------------|
| **fastest** / **fast** | ViT-B-32::laion2b_e16 |
| **balanced** (default) | ViT-L-14::laion2b_s32b_b82k |
| **best** / **nextbest** | ViT-H-14::laion2B-s32B-b79K |
| **newbest** | ViT-bigG-14::laion2B-s39B-b160K |
| **semantic** | ViT-B-16::openai |
| **siglip** | ViT-SO400M-14-SigLIP-384::webli |
| **newest** | Same as **best** (LAION ViT-H; DINOv2 not wired here) |

You can also set `MODEL_PRESET` to a raw OpenCLIP id, e.g. `ViT-H-14::laion2B-s32B-b79K`.

## Retrieval tuning (optional env)

| Variable | Default | Meaning |
|----------|---------|---------|
| `SIMILARITY_THRESHOLD` | `0.35` | Minimum cosine similarity to keep a hit; `-1` disables filtering |
| `RETRIEVAL_CANDIDATES_K` | `50` | Internal Pinecone `top_k` before re-rank / threshold / client `top_k` trim |
| `RETRIEVAL_MIN_RESULTS_FALLBACK` | `2` | If fewer hits, widen filter then drop filter |
| `RETRIEVAL_METADATA_BOOST` | `0.04` | Score boost when title/description matches family keywords |
| `EMBEDDER_MULTI_CROP` | unset | Set to `1` / `true` to average default + center-crop embeddings |
| `PINECONE_NAMESPACE` | `__default__` | Pinecone namespace for query/upsert |

## Offline retrieval eval

```bash
cd backend
python scripts/eval_retrieval.py --manifest ../data/eval_manifest.example.json --k 1,5,10
```

Populate `queries` with `image_url`, `relevant_ids` (Pinecone vector ids), and `search_family` for filtered-vs-unfiltered metrics. Use `--preset siglip` or `--multi-crop` to compare embedding setups.

## Example Usage

### Python Client

```python
import requests

# Upload images
files = [
    ('files', open('sofa1.jpg', 'rb')),
    ('files', open('sofa2.jpg', 'rb'))
]
response = requests.post('http://localhost:8000/api/upload', files=files)
print(response.json())

# Search for similar
files = {'file': open('query.jpg', 'rb')}
response = requests.post('http://localhost:8000/api/search?top_k=5', files=files)
print(response.json())
```

### cURL

```bash
# Upload
curl -X POST "http://localhost:8000/api/upload" \\
  -F "files=@sofa1.jpg" \\
  -F "files=@sofa2.jpg"

# Search
curl -X POST "http://localhost:8000/api/search?top_k=5" \\
  -F "file=@query.jpg"
```

## Cost Estimation (Modal)

- **T4 GPU**: ~$0.60/hour when running
- **Cold start**: Free (included)
- **Idle timeout**: Configurable (default: 5 min)
- **Pay-per-use**: Only charged when processing requests

## Troubleshooting

### GPU Memory Issues
If you get OOM errors, switch to a smaller model:
```
MODEL_PRESET=fast
```

### Pinecone Connection Issues
- Verify API key is correct
- Check region matches your Pinecone index
- Ensure index name is unique

### Slow First Request
Cold start on Modal takes 20-60 seconds for model loading. Subsequent requests are fast.

## License

MIT License