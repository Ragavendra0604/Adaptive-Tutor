from pydantic_settings import BaseSettings
from pathlib import Path
import os
from typing import Optional

ENV_FILE_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str = "" 
    MONGO_URI: str = ""

    MONGO_DB: str = ""
    EMBEDDING_MODEL: str = ""
    FAISS_INDEX_PATH: str = ""
    EMBEDDING_DIM: int = 384

    openrouter_api_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    openrouter_api_url: Optional[str] = None
    judge0_url: Optional[str] = None
    judge0_api_key: Optional[str] = None
    
    class Config:
        env_file = ENV_FILE_PATH
        env_file_encoding = 'utf-8'

settings = Settings()

if not settings.OPENROUTER_API_KEY:
    print("!!!!!!!!!!!! WARNING !!!!!!!!!!!!!")
    print(f"Could not load OPENAI_API_KEY from {ENV_FILE_PATH}")
    print("Please check your .env file.")