from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o"
    ai_service_port: int = 8000
    ai_service_host: str = "0.0.0.0"
    grpc_server_url: str = "localhost:50051"
    max_tokens: int = 2048
    temperature: float = 0.2
    
    class Config:
        env_file = ".env"

settings = Settings()
