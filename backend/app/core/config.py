# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

# distinct path logic to find .env in the root folder
ENV_FILE_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    # --- OPENROUTER / LLM ---
    OPENROUTER_API_KEY: Optional[str]
    OPENROUTER_MODEL: str
    OPENROUTER_API_URL: Optional[str]

    # --- JUDGE0 ---
    JUDGE0_API_URL: str
    JUDGE0_API_KEY: Optional[str] = None
    JUDGE0_API_HOST: str

    # --- VECTOR / EMBEDDINGS ---
    EMBEDDING_MODEL: str
    EMBEDDING_DIM: int
    FAISS_INDEX_PATH: str

    # --- DATABASE ---
    MONGO_URI: str
    MONGO_DB: str

    # FIX: Use ONLY model_config (Pydantic V2 style)
    # We merge the logic: point to ENV_FILE_PATH, set encoding, and ignore extras.
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# WARNING if API key missing
if not settings.OPENROUTER_API_KEY:
    print("!!!!!!!!!!!! WARNING !!!!!!!!!!!!!")
    print(f"Could not load OPENROUTER_API_KEY from {ENV_FILE_PATH}")
    print("Please check your .env file.")