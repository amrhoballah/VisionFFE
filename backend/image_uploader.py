import uuid
import os

class ImageUploader:
    def __init__(self, s3_client, bucket_name, embedder, index):
        self.s3_client = s3_client
        self.bucket_name = bucket_name
        self.embedder = embedder
        self.index = index

    async def upload_image(self, file, folder_name):
        try:
            file_bytes = await file.read()
            # Generate unique filename with same extension
            file_ext = os.path.splitext(file.filename)[1]
            unique_name = f"{uuid.uuid4().hex}{file_ext}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"{folder_name}/{unique_name}",
                Body=file_bytes,
                ContentType=file.content_type
            )

            file_url = f"{os.getenv('R2_URL')}/{f"{folder_name}/{unique_name}"}"
            return file_url
        except Exception as e:
            print(f"Failed to upload image {file.filename}: {e}")
            
    async def upload_bytes(self, data: bytes, folder_name: str, filename: str = "image.jpg"):
        """Upload raw bytes data to S3 storage"""
        try:
            # Extract file extension from filename
            # file_ext = os.path.splitext(filename)[1] or ".jpg"
            unique_name = f"{uuid.uuid4().hex}"
            
            # Determine content type based on extension
            content_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            content_type = "image/png",
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"{folder_name}/{unique_name}",
                Body=data,
                ContentType=content_type
            )
            file_url = f"{os.getenv('R2_URL')}/{folder_name}/{unique_name}"
            return file_url
        except Exception as e:
            print(f"Failed to upload bytes: {e}")
            return None

    async def delete_image(self, file_url: str) -> bool:
        """Delete an image from R2 storage based on its URL"""
        try:
            # Extract the key from the URL
            # URL format: https://r2-url.com/projects/123/abc123.jpg
            # We need: projects/123/abc123.jpg
            r2_url = os.getenv('R2_URL', '')
            if not r2_url or not file_url.startswith(r2_url):
                print(f"Invalid R2 URL format: {file_url}")
                return False
            
            # Get the key by removing the base URL
            key = file_url.replace(r2_url + '/', '')
            
            # Delete the object from R2
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            print(f"Successfully deleted image from R2: {key}")
            return True
        except Exception as e:
            print(f"Failed to delete image from R2: {e}")
            return False

    async def add_furniture_item(self, file, metadata):
        try:
            file_url = await self.upload_image(file, "furniture")
            
            embedding = self.embedder.get_embedding(file_url)
            if embedding is None:
                print(f"Failed to get embedding for image {unique_name}")
                return False
            
            metadata["image_url"] = file_url
            
            self.index.upsert(
                vectors=[
                    {
                    "id": unique_name, 
                    "values": embedding.tolist(), 
                    "metadata": metadata
                    }
                ],
                namespace="__default__"
            )
            return True
        
        except Exception as e:
            print(f"Failed to upload image {unique_name}: {e}")
            return False
        

    async def search_item(self, file):
        try:
            file_bytes = await file.read()
            # Generate unique filename with same extension
            file_ext = os.path.splitext(file.filename)[1]
            unique_name = f"{uuid.uuid4().hex}{file_ext}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_name,
                Body=file_bytes,
                ContentType=file.content_type
            )

            file_url = f"{os.getenv('R2_URL')}/{unique_name}"
            
            embedding = self.embedder.get_embedding(file_url)
            if embedding is None:
                print(f"Failed to get embedding for image {unique_name}")
                return False
    
            return embedding
        
        except Exception as e:
            print(f"Failed to upload image {unique_name}: {e}")
            return False