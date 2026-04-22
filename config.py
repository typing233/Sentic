from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: str = "your_openai_api_key_here"
    openai_model: str = "gpt-4-turbo-preview"
    
    database_url: str = "sqlite:///./sentic.db"
    
    app_name: str = "数字分析科学家"
    app_version: str = "2.0.0"
    debug: bool = True
    
    host: str = "0.0.0.0"
    port: int = 8000
    
    secret_key: str = "sentic-secret-key-2024-change-in-production"
    access_token_expire_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
