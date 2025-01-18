import os
from typing import List, Dict
from atlassian import Confluence
from langchain.document_loaders import ConfluenceLoader
from langchain.schema import Document
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
from src.database.db import get_db_connection
from src.document_processing.processor import DocumentProcessor

load_dotenv()

class ConfluenceKnowledgeBase:
    def __init__(self):
        self.confluence_url = os.getenv("CONFLUENCE_URL")
        self.confluence_username = os.getenv("CONFLUENCE_USERNAME")
        self.confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")
        self.space_key = os.getenv("CONFLUENCE_SPACE_KEY")
        
        if not all([self.confluence_url, self.confluence_username, 
                   self.confluence_api_token, self.space_key]):
            raise ValueError("Missing required Confluence environment variables")
        
        self.confluence = Confluence(
            url=self.confluence_url,
            username=self.confluence_username,
            password=self.confluence_api_token,
            cloud=True
        )
        
        self.loader = ConfluenceLoader(
            url=self.confluence_url,
            username=self.confluence_username,
            api_key=self.confluence_api_token
        )
        
        self.doc_processor = DocumentProcessor()

    def load_space_content(self) -> List[Document]:
        """Load all content from the specified Confluence space"""
        try:
            documents = self.loader.load(
                space_key=self.space_key,
                include_attachments=False,
                limit=50  # Adjust based on your needs
            )
            return documents
        except Exception as e:
            print(f"Error loading Confluence content: {str(e)}")
            return []

    def process_and_store_documents(self, documents: List[Document]):
        """Process documents and store them in the database"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            for doc in documents:
                # Store the original document
                cur.execute(
                    """
                    INSERT INTO documents (title, content, source, created_at, user_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        doc.metadata.get('title', 'Untitled'),
                        doc.page_content,
                        f"confluence:{self.space_key}",
                        datetime.now(),
                        'confluence'
                    )
                )
                doc_id = cur.fetchone()[0]
                
                # Split into chunks and store
                chunks = self.doc_processor.split_text(doc.page_content)
                chunk_embeddings = self.doc_processor.generate_embeddings(chunks)
                
                for chunk_text, embedding, _ in chunk_embeddings:
                    cur.execute(
                        """
                        INSERT INTO chunks (document_id, content, embedding)
                        VALUES (%s, %s, %s)
                        """,
                        (doc_id, chunk_text, embedding.tolist())
                    )
            
            conn.commit()
            print(f"Successfully processed and stored {len(documents)} documents")
            
        except Exception as e:
            print(f"Error processing and storing documents: {str(e)}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    def run(self):
        """Main function to load and process Confluence content"""
        print("Starting Confluence content loading...")
        documents = self.load_space_content()
        if documents:
            print(f"Loaded {len(documents)} documents from Confluence")
            self.process_and_store_documents(documents)
        else:
            print("No documents were loaded from Confluence")

if __name__ == "__main__":
    confluence_kb = ConfluenceKnowledgeBase()
    confluence_kb.run()
