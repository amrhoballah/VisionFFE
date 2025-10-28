import uuid
import os

class ImageUploader:
    def __init__(self, s3_client, bucket_name, embedder, index):
        self.s3_client = s3_client
        self.bucket_name = bucket_name
        self.embedder = embedder
        self.index = index

    async def add_furniture_item(self, file, metadata):
        try:
            file_bytes = await file.read()
            # Generate unique filename with same extension
            file_ext = os.path.splitext(file.filename)[1]
            unique_name = f"{uuid.uuid4().hex}{file_ext}"
            # Store in uploads folder
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"noise/{unique_name}",
                Body=file_bytes,
                ContentType=file.content_type
            )

            file_url = f"{os.getenv('R2_URL')}/noise/{unique_name}"
            
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
            # Store search queries in temp folder
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"temp/{unique_name}",
                Body=file_bytes,
                ContentType=file.content_type
            )

            file_url = f"{os.getenv('R2_URL')}/temp/{unique_name}"
            
            # embedding = self.embedder.get_embedding(file_url)
            # if embedding is None:
            #     print(f"Failed to get embedding for image {unique_name}")
            #     return False
    
            return file_url
        
        except Exception as e:
            print(f"Failed to upload image {unique_name}: {e}")
            return False