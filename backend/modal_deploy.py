import modal
import os
import sys

# Create Modal image with dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        [
            "fastapi",
            "uvicorn[standard]",
            "python-multipart",
            "torch",
            "torchvision",
            "timm",
            "pillow",
            "numpy",
            "scikit-learn",
            "pinecone",
            "python-dotenv",
            "boto3",
            "botocore",
            "pinecone[asyncio]",
            "transformers==4.49.0",
            "huggingface-hub",
            "open-clip-torch",
            # Authentication dependencies
            "python-jose[cryptography]",
            "passlib[argon2]",
            "motor",
            "pymongo",
            "pydantic",
            "pydantic-settings",
            "email-validator",
            "beanie",
            "certifi",
            "google-genai",
            "einops"
        ]
    )
    # ✅ Copy everything in your current folder into /root/app
    .add_local_dir(".", "/root/app")
)

app = modal.App("vision-ffe-api", image=image)

data_volume = modal.Volume.from_name("furniture-data", create_if_missing=True)

@app.function(
    gpu="T4",
    secrets=[modal.Secret.from_name("vision-api")],
    timeout=900,
    volumes={"/data": data_volume},
    scaledown_window=300,  # replaces old container_idle_timeout
)
@modal.asgi_app()
def fast_app():
    # ✅ Confirm environment
    print("Current working directory:", os.getcwd())
    print("Files in /root:", os.listdir("/root"))
    print("Files in /root/app:", os.listdir("/root/app"))

    # ✅ Ensure Python can find your app code
    sys.path.append("/root/app")

    # ✅ Import FastAPI app from main.py
    from main import app as fastapi_app

    return fastapi_app
