"""Document processing utilities for text extraction and embedding generation."""
import pypdf
from typing import List, Tuple
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import AzureOpenAIEmbeddings
import os
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        """Initialize document processor with Azure OpenAI embeddings."""
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment=os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"),
            openai_api_type="azure",
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            chunk_size=16
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def process_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        try:
            return self.text_splitter.split_text(text)
        except Exception as e:
            logger.error(f"Error splitting text: {str(e)}")
            raise

    def generate_embeddings(self, chunks: List[str]) -> List[Tuple[str, np.ndarray, int]]:
        """Generate embeddings for text chunks."""
        try:
            embeddings = self.embeddings.embed_documents(chunks)
            return [(chunk, np.array(emb), idx) for idx, (chunk, emb) in enumerate(zip(chunks, embeddings))]
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    def generate_query_embedding(self, query: str) -> np.ndarray:
        """Generate embedding for a query string."""
        try:
            embedding = self.embeddings.embed_query(query)
            return np.array(embedding)
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
