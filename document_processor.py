import os
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from io import BytesIO
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Log environment variables
        logger.info("Initializing DocumentProcessor with:")
        logger.info(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        logger.info(f"OPENAI_API_VERSION: {os.getenv('OPENAI_API_VERSION')}")
        logger.info(f"AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT: {os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT')}")
        logger.info(f"AZURE_OPENAI_CHAT_DEPLOYMENT_NAME: {os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT_NAME')}")
        logger.info(f"AZURE_OPENAI_API_KEY: {os.getenv('AZURE_OPENAI_API_KEY')}")
        
        # Create embeddings instance with explicit values for debugging
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("OPENAI_API_VERSION")
        deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        logger.info(f"Creating AzureOpenAIEmbeddings with:")
        logger.info(f"endpoint: {endpoint}")
        logger.info(f"api_version: {api_version}")
        logger.info(f"deployment: {deployment}")
        
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=endpoint,
            openai_api_version=api_version,
            azure_deployment=deployment,
            api_key=api_key,
            chunk_size=1000
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def process_pdf(self, pdf_file) -> str:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text

    def process_url(self, url: str) -> str:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text()

    def split_text(self, text: str) -> List[str]:
        return self.text_splitter.split_text(text)

    def generate_embeddings(self, chunks: List[str]) -> List[Tuple[str, np.ndarray, int]]:
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        try:
            embeddings = self.embeddings.embed_documents(chunks)
            logger.info(f"Successfully generated embeddings")
            logger.info(f"First embedding shape: {np.array(embeddings[0]).shape}")
            logger.info(f"First embedding length: {len(embeddings[0])}")
            return [(chunk, np.array(embedding), i) for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))]
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            raise

    def generate_query_embedding(self, query: str) -> np.ndarray:
        return np.array(self.embeddings.embed_query(query))
