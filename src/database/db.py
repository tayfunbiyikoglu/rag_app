"""Database operations for document storage and retrieval."""
import psycopg2
from psycopg2.extensions import register_adapter
import numpy as np
from typing import List, Tuple, Optional
import logging
import os

logger = logging.getLogger(__name__)

def adapt_array(arr):
    """Convert numpy array to a format suitable for PostgreSQL vector type."""
    return f"[{','.join(map(str, arr.astype(float)))}]"

register_adapter(np.ndarray, adapt_array)

class Database:
    def __init__(self):
        """Initialize database connection."""
        self.conn = None
        logger.info("Initializing database connection...")
        self.connect()
        self._create_tables()

    def connect(self):
        """Connect to the database."""
        logger.info("Connecting to database...")
        if self.conn is None or self.conn.closed:
            try:
                self.conn = psycopg2.connect(
                    host=os.getenv("POSTGRES_HOST"),
                    port=os.getenv("POSTGRES_PORT"),
                    database=os.getenv("POSTGRES_DB"),
                    user=os.getenv("POSTGRES_USER"),
                    password=os.getenv("POSTGRES_PASSWORD")
                )
                logger.info("Successfully connected to database")
            except Exception as e:
                logger.error(f"Error connecting to database: {str(e)}")
                raise

    def ensure_connection(self):
        """Ensure that we have a valid database connection."""
        if self.conn is None or self.conn.closed:
            logger.info("Connection is None or closed, reconnecting...")
            self.connect()
            return

        try:
            # Try a simple query to test the connection
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.warning(f"Connection test failed: {str(e)}, reconnecting...")
            self.connect()

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            # Create vector extension if it doesn't exist
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Create documents table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    source TEXT,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create chunks table with vector support
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(id),
                    content TEXT,
                    embedding vector(1536),
                    chunk_index INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def insert_document(self, title: str, source: str, user_id: str) -> int:
        """Insert a new document and return its ID."""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO documents (title, source, user_id) VALUES (%s, %s, %s) RETURNING id",
                (title, source, user_id)
            )
            doc_id = cur.fetchone()[0]
            self.conn.commit()
            return doc_id

    def insert_chunks(self, doc_id: int, chunks: List[Tuple[str, np.ndarray, int]]):
        """Insert document chunks with their embeddings."""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            for content, embedding, chunk_index in chunks:
                embedding_str = adapt_array(embedding)
                cur.execute(
                    """
                    INSERT INTO chunks (document_id, content, embedding, chunk_index)
                    VALUES (%s, %s, %s::vector, %s)
                    """,
                    (doc_id, content, embedding_str, chunk_index)
                )
            self.conn.commit()

    def get_user_documents(self, user_id: str) -> List[Tuple[int, str, str]]:
        """Get all documents for a specific user."""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, source FROM documents WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            return cur.fetchall()

    def search_similar_chunks(
        self, 
        query_embedding: np.ndarray, 
        limit: int = 5, 
        user_id: Optional[str] = None,
        document_id: Optional[int] = None
    ) -> List[Tuple[str, str, float]]:
        """Search for similar chunks using cosine similarity."""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            # Convert embedding to string format
            embedding_str = adapt_array(query_embedding)
            
            # Build the query
            query = """
                SELECT c.content, d.title, (c.embedding <=> %s::vector) as distance
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE 1=1
            """
            params = [embedding_str]
            
            if user_id:
                query += " AND d.user_id = %s"
                params.append(user_id)

            if document_id:
                query += " AND d.id = %s"
                params.append(document_id)
                
            query += """
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
            """
            params.extend([embedding_str, limit])
            
            # Execute query
            cur.execute(query, params)
            results = cur.fetchall()
            return [(content, title, float(distance)) for content, title, distance in results]

    def close(self):
        """Close the database connection."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
