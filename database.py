import os
from typing import List, Tuple
import psycopg2
from psycopg2.extensions import register_adapter
import numpy as np
from dotenv import load_dotenv
import json

load_dotenv()

def adapt_array(arr):
    """
    Convert numpy array to a format suitable for PostgreSQL vector type.
    """
    return f"[{','.join(map(str, arr.astype(float)))}]"

register_adapter(np.ndarray, adapt_array)

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        self._create_tables()

    def _create_tables(self):
        with self.conn.cursor() as cur:
            # Create vector extension if it doesn't exist
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Drop existing tables if they exist
            cur.execute("DROP TABLE IF EXISTS chunks")
            cur.execute("DROP TABLE IF EXISTS documents")
            
            # Create documents table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create chunks table with vector support
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(id),
                    content TEXT,
                    embedding vector(3072),
                    chunk_index INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def insert_document(self, title: str, source: str) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO documents (title, source) VALUES (%s, %s) RETURNING id",
                (title, source)
            )
            document_id = cur.fetchone()[0]
            self.conn.commit()
            return document_id

    def insert_chunks(self, document_id: int, chunks: List[Tuple[str, np.ndarray, int]]):
        with self.conn.cursor() as cur:
            for content, embedding, chunk_index in chunks:
                embedding_str = adapt_array(embedding)
                cur.execute(
                    """
                    INSERT INTO chunks (document_id, content, embedding, chunk_index)
                    VALUES (%s, %s, %s::vector, %s)
                    """,
                    (document_id, content, embedding_str, chunk_index)
                )
            self.conn.commit()

    def search_similar_chunks(self, query_embedding: np.ndarray, limit: int = 5) -> List[Tuple[str, float]]:
        with self.conn.cursor() as cur:
            embedding_str = adapt_array(query_embedding)
            cur.execute(
                """
                SELECT content, 1 - (embedding <=> %s::vector) as similarity
                FROM chunks
                ORDER BY similarity DESC
                LIMIT %s
                """,
                (embedding_str, limit)
            )
            return cur.fetchall()

    def close(self):
        self.conn.close()
