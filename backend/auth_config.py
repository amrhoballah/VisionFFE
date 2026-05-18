from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class AuthSettings(BaseSettings):
    # JWT Settings (env: JWT_SECRET_KEY)
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        validation_alias="JWT_SECRET_KEY",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7

    # MongoDB Settings
    mongodb_url: str = Field(default="mongodb://localhost:27017")
    mongodb_database: str = Field(default="visionffe_auth")
    
    # Password Settings
    password_min_length: int = 8
    
    # CORS Settings
    # allowed_origins: list = ["http://localhost:3000", "http://localhost:8080", "https://vision-ffe.vercel.app"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


auth_settings = AuthSettings()
