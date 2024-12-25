# RAG Application

This is a Retrieval Augmented Generation (RAG) application that allows users to upload documents and chat with them using Azure OpenAI's GPT-4 model.

## Features

### Admin Interface
- Upload PDF documents or provide URLs
- Automatic document splitting and embedding generation
- Storage of document chunks and embeddings in PostgreSQL with pgvector

### Chat Interface
- Natural language question answering
- Semantic search for relevant document chunks
- Conversational interface with chat history

## Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension
- Azure OpenAI API access

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Copy `.env.template` to `.env` and fill in your configuration:
```bash
cp .env.template .env
```

4. Update the `.env` file with your credentials:
- Azure OpenAI API credentials
- PostgreSQL database configuration

## Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

## Usage

1. **Admin Interface (Sidebar)**
   - Choose between uploading a PDF file or providing a URL
   - Upload/process documents to add them to the knowledge base

2. **Chat Interface (Main Area)**
   - Type your questions in the chat input
   - View the conversation history
   - Get AI-generated responses based on your documents

## Project Structure

- `app.py`: Main Streamlit application
- `database.py`: PostgreSQL database utilities
- `document_processor.py`: Document processing and embedding generation
- `chat.py`: Chat interface and response generation
- `requirements.txt`: Python dependencies
- `.env.template`: Template for environment variables
