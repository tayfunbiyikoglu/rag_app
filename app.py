import streamlit as st
from database import Database
from document_processor import DocumentProcessor
from chat import ChatBot
import tempfile
from typing import List, Tuple
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

# Log environment variables at startup
logger.info("Environment variables after loading .env:")
logger.info(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
logger.info(f"OPENAI_API_VERSION: {os.getenv('OPENAI_API_VERSION')}")
logger.info(f"AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT: {os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT')}")
logger.info(f"AZURE_OPENAI_CHAT_DEPLOYMENT_NAME: {os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT_NAME')}")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "db" not in st.session_state:
    st.session_state.db = Database()
if "doc_processor" not in st.session_state:
    st.session_state.doc_processor = DocumentProcessor()
if "chatbot" not in st.session_state:
    st.session_state.chatbot = ChatBot()
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()
if "user_id" not in st.session_state:
    st.session_state.user_id = "default_user"

# Use session state components
db = st.session_state.db
doc_processor = st.session_state.doc_processor
chatbot = st.session_state.chatbot

st.title("Chat with Your Documents")

# Sidebar for admin interface
with st.sidebar:
    # st.header("Admin Interface")

    # Add user_id input field
    user_id = st.text_input("User ID:", value=st.session_state.user_id)
    if user_id != st.session_state.user_id:
        st.session_state.user_id = user_id
        st.session_state.processed_files = set()  # Clear processed files when user changes

    # Get user's documents
    if st.session_state.user_id:
        documents = db.get_user_documents(st.session_state.user_id)
        if documents:
            # Create options list with "All Documents" as first option
            doc_options = [("all", "All Documents")] + [(str(id), title) for id, title, _ in documents]
            selected_doc = st.selectbox(
                "Select Document:",
                options=[id for id, _ in doc_options],
                format_func=lambda x: dict(doc_options)[x],
                key="selected_document"
            )
        else:
            st.info("No documents found. Please upload a document first.")
            selected_doc = None
    else:
        st.info("Please enter a User ID to see your documents.")
        selected_doc = None

    st.divider()

    # PDF Upload Section
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    process_pdf = st.button("Process PDF", disabled=not uploaded_file)

    if uploaded_file and process_pdf:
        file_key = f"pdf_{uploaded_file.name}_{st.session_state.user_id}"
        if file_key not in st.session_state.processed_files:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                text = doc_processor.process_pdf(tmp_file.name)
                st.success("PDF processed successfully!")

                with st.spinner("Processing document..."):
                    # Split text into chunks
                    chunks = doc_processor.split_text(text)

                    # Generate embeddings
                    chunk_embeddings = doc_processor.generate_embeddings(chunks)

                    # Store in database with user_id
                    doc_id = db.insert_document(uploaded_file.name, "pdf", st.session_state.user_id)
                    db.insert_chunks(doc_id, chunk_embeddings)

                    # Mark as processed
                    st.session_state.processed_files.add(file_key)
                    st.success("Document indexed successfully!")

# Main chat interface
# st.header("Chat Interface")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents"):
    if not selected_doc:
        st.error("Please select a document to chat with.")
    else:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Get query embedding
        query_embedding = doc_processor.generate_query_embedding(prompt)

        # Search for similar chunks with user_id filter and optional document filter
        similar_chunks = db.search_similar_chunks(
            query_embedding,
            limit=5,
            user_id=st.session_state.user_id,
            document_id=None if selected_doc == "all" else int(selected_doc)
        )

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Extract content from similar chunks
        context = []
        if similar_chunks:
            for content, title, distance in similar_chunks:
                context.append(f"From document '{title}': {content}")

        # Display assistant message placeholder
        with st.chat_message("assistant"):
            # Create a placeholder for the streaming response
            response_placeholder = st.empty()
            
            # Generate streaming response
            response = chatbot.generate_response(
                query=prompt,
                context=context,
                chat_history=st.session_state.chat_history,
                response_placeholder=response_placeholder
            )

        # Add assistant's message to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})

        # Display assistant's message
        with st.chat_message("assistant"):
            st.write(response)

# Cleanup
db.close()
