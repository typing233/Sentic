from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # OpenAI API配置
    openai_api_key: str = "your_openai_api_key_here"
    openai_model: str = "gpt-4-turbo-preview"
    
    # 数据库配置
    database_url: str = "sqlite:///./test.db"
    
    # 应用配置
    app_name: str = "数字分析科学家"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
