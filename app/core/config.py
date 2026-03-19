# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # NO defaults here — must come from .env
    CHUNKER_URL:  str
    EMBED_URL:    str
    STORE_URL:    str
    SEARCH_URL:   str
    OLLAMA_URL:   str
    OLLAMA_MODEL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()