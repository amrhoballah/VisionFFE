# Furniture Image Similarity Search API

AI-powered furniture image similarity search using deep learning and Pinecone vector database.

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

## Model Presets

- **best**: Highest accuracy, slower (ConvNeXt V2 Huge)
- **balanced**: Great accuracy, reasonable speed (ConvNeXt V2 Base) ⭐ Recommended
- **fast**: Fast processing (EfficientNet B3)
- **fastest**: Fastest, lower accuracy (MobileNet V3)
- **semantic**: Best for concept understanding (CLIP ViT)

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