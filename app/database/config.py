# DB CONNECTION
import psycopg2
from pgvector.psycopg2 import register_vector


DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "legal_db",
    "user": "postgres",
    "password": "postgres"
}

def get_connection():
    """
    Creates and returns a fresh DB connection.
    Also registers the vector type so psycopg2
    understands pgvector columns.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    register_vector(conn)   # ← tells psycopg2 how to handle vector type
    return conn
