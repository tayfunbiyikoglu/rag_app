import os
from typing import List, Tuple
import numpy as np
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

class DocumentProcessor:
    def __init__(self):
        logger.info("Initializing DocumentProcessor...")
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("OPENAI_API_VERSION"),
            deployment=os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"),
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def process_pdf(self, file_path: str) -> str:
        """
        Process a PDF file and extract its text content.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text content from the PDF
            
        Raises:
            Exception: If there's an error processing the PDF
        """
        logger.info(f"Processing PDF file: {file_path}")
        try:
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            return "\n".join(page.page_content for page in pages)
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    def split_text(self, text: str) -> List[str]:
        """
        Split text into smaller chunks for processing.
        
        Args:
            text (str): Text to split
            
        Returns:
            List[str]: List of text chunks
            
        Raises:
            Exception: If there's an error splitting the text
        """
        logger.info("Splitting text into chunks")
        try:
            return self.text_splitter.split_text(text)
        except Exception as e:
            logger.error(f"Error splitting text: {str(e)}")
            raise

    def generate_embeddings(self, chunks: List[str]) -> List[Tuple[str, np.ndarray, int]]:
        """
        Generate embeddings for a list of text chunks.
        
        Args:
            chunks (List[str]): List of text chunks to generate embeddings for
            
        Returns:
            List[Tuple[str, np.ndarray, int]]: List of tuples containing:
                - Original text chunk
                - Embedding vector as numpy array
                - Chunk index
                
        Raises:
            Exception: If there's an error generating embeddings
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        try:
            embeddings = self.embeddings.embed_documents(chunks)
            logger.info(f"Successfully generated embeddings")
            logger.info(f"First embedding shape: {np.array(embeddings[0]).shape}")
            return [(chunk, np.array(embedding), i) for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))]
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query string.
        
        Args:
            query (str): Query text
            
        Returns:
            np.ndarray: Embedding vector for the query
        """
        return np.array(self.embeddings.embed_query(query))
