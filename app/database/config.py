# app/database/config.py
import psycopg2
from pgvector.psycopg2 import register_vector
from pydantic_settings import BaseSettings

class DBSettings(BaseSettings):
    # NO defaults — must come from .env
    DB_HOST:     str
    DB_PORT:     int
    DB_NAME:     str
    DB_USER:     str
    DB_PASSWORD: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

db_settings = DBSettings()

DB_CONFIG = {
    "host":     db_settings.DB_HOST,
    "port":     db_settings.DB_PORT,
    "dbname":   db_settings.DB_NAME,
    "user":     db_settings.DB_USER,
    "password": db_settings.DB_PASSWORD
}

def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    register_vector(conn)
    return conn