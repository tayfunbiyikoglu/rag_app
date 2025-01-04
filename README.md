# RAG Applications Suite

This repository contains two Retrieval Augmented Generation (RAG) applications:
1. Document Chat: Chat with your uploaded documents using Azure OpenAI
2. Adverse News Analysis: Search and analyze adverse news about financial institutions

## Features

### Document Chat Application
- Upload and process PDF documents
- Chat with your documents using natural language
- Semantic search for relevant document chunks
- Conversational interface with chat history
- Multi-user support with document isolation

### Adverse News Analysis Application
- Search for adverse news about financial institutions
- Advanced news filtering and analysis
- Comprehensive scoring system for news severity
- Detailed analysis of misconduct, penalties, and regulatory actions
- Integration with SerpAPI for real-time news search
- Azure OpenAI-powered content analysis

## Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension
- Azure OpenAI API access
- SerpAPI key (for adverse news analysis)

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

3. Copy `.env.example` to `.env` and fill in your configuration:
```bash
cp .env.example .env
```

4. Update the `.env` file with your credentials:
```
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your-embeddings-deployment
OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=your-chat-deployment
AZURE_OPENAI_MODEL_NAME=your-model-name
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=your-embeddings-deployment

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your-db-name
POSTGRES_USER=your-username
POSTGRES_PASSWORD=your-password

# Search Configuration
SERPAPI_KEY=your-serpapi-key
```

## Running the Applications

### Document Chat Application
```bash
streamlit run chat_app.py
```

### Adverse News Analysis Application
```bash
streamlit run adverse.py
```

## Project Structure

```
rag_app/
├── src/
│   ├── chat/                    # Document chat application
│   │   ├── __init__.py
│   │   ├── app.py              # Main chat application logic
│   │   └── chatbot.py          # ChatBot implementation
│   ├── database/               # Database operations
│   │   ├── __init__.py
│   │   └── db.py
│   ├── document_processing/    # Document processing utilities
│   │   ├── __init__.py
│   │   └── processor.py
│   ├── services/              # Adverse news services
│   │   ├── __init__.py
│   │   ├── analysis_service.py # News content analysis
│   │   └── search_service.py   # News search functionality
│   └── config/                # Configuration
│       └── settings.py        # Application settings
├── chat_app.py               # Entry point for document chat
├── adverse.py               # Entry point for adverse news analysis
├── requirements.txt         # Python dependencies
└── .env.example            # Environment variables template
```

## Usage

### Document Chat Application
1. Start the application using `streamlit run chat_app.py`
2. Enter your user ID in the sidebar
3. Upload PDF documents using the file uploader
4. Select a document to chat with
5. Ask questions about your documents in natural language

### Adverse News Analysis Application
1. Start the application using `streamlit run adverse.py`
2. Enter the name of a financial institution
3. Set the desired search parameters (date range, result count)
4. Click "Search" to find adverse news
5. View the analysis results and detailed scoring
6. Access individual news articles and their severity scores

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
