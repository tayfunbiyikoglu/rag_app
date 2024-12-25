import os
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from io import BytesIO
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import AzureOpenAIEmbeddings

class DocumentProcessor:
    def __init__(self):
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
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
        embeddings = self.embeddings.embed_documents(chunks)
        return [(chunk, np.array(embedding), i) for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))]

    def generate_query_embedding(self, query: str) -> np.ndarray:
        return np.array(self.embeddings.embed_query(query))
