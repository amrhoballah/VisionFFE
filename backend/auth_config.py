from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class AuthSettings(BaseSettings):
    # JWT Settings
    secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7
    
    # MongoDB Settings
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "visionffe_auth")
    
    # Password Settings
    password_min_length: int = 8
    
    # CORS Settings
    # allowed_origins: list = ["http://localhost:3000", "http://localhost:8080", "https://vision-ffe.vercel.app"]
    
    model_config = ConfigDict(env_file=".env")

auth_settings = AuthSettings()
