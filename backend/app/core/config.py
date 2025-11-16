from pydantic_settings import BaseSettings
from pathlib import Path

ENV_FILE_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # --- OPENROUTER / LLM ---
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str
    OPENROUTER_API_URL: str

    # --- JUDGE0 ---
    JUDGE0_URL: str
    JUDGE0_API_KEY: str

    # --- VECTOR / EMBEDDINGS ---
    EMBEDDING_MODEL: str
    EMBEDDING_DIM: int = 384
    FAISS_INDEX_PATH: str

    # --- DATABASE ---
    MONGO_URI: str
    MONGO_DB: str

    class Config:
        env_file = ENV_FILE_PATH
        env_file_encoding = "utf-8"


settings = Settings()

# WARNING if API key missing
if not settings.OPENROUTER_API_KEY:
    print("!!!!!!!!!!!! WARNING !!!!!!!!!!!!!")
    print(f"Could not load OPENROUTER_API_KEY from {ENV_FILE_PATH}")
    print("Please check your .env file.")