"""Main Streamlit application for document chat interface."""
import streamlit as st
from typing import List, Tuple
import tempfile
import logging
from dotenv import load_dotenv
import os

from ..database.db import Database
from ..document_processing.processor import DocumentProcessor
from .chatbot import ChatBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

def init_session_state():
    """Initialize session state variables."""
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
    if "last_uploaded_doc_id" not in st.session_state:
        st.session_state.last_uploaded_doc_id = None

def on_user_change():
    """Handle user ID change."""
    st.session_state.user_id = st.session_state.user_id_input
    st.session_state.processed_files = set()
    st.session_state.chat_history = []

def setup_document_interface():
    """Setup document interface with user controls."""
    with st.expander("**Select or Upload Your Documents**", expanded=False):
        # User ID input
        col1, col2 = st.columns([2, 3])
        with col1:
            st.text_input(
                "User ID:",
                value=st.session_state.user_id,
                key="user_id_input",
                on_change=on_user_change
            )

        # Document selection and upload
        documents = st.session_state.db.get_user_documents(st.session_state.user_id)
        selected_doc = None

        with col2:
            if documents:
                doc_options = [("all", "All Documents")] + [(str(id), title) for id, title, _ in documents]
                # Use the last uploaded document as the default if available
                default_index = 0
                if st.session_state.last_uploaded_doc_id:
                    for i, (doc_id, _) in enumerate(doc_options):
                        if doc_id == str(st.session_state.last_uploaded_doc_id):
                            default_index = i
                            break

                selected_doc = st.selectbox(
                    "Select Document:",
                    options=[id for id, _ in doc_options],
                    format_func=lambda x: dict(doc_options)[x],
                    key="selected_document",
                    index=default_index
                )
                # Reset last_uploaded_doc_id after it's been used
                st.session_state.last_uploaded_doc_id = None
            else:
                st.write("")  # Add vertical spacing
                st.info("No documents found. Please upload a document first.")

        st.write("")  # Add spacing between rows

        # File upload section with aligned button
        col3, col4 = st.columns([3, 1])
        with col3:
            # Initialize the file uploader key in session state if not present
            if "file_uploader_key" not in st.session_state:
                st.session_state.file_uploader_key = 0
                
            uploaded_file = st.file_uploader(
                "Upload PDF",
                type="pdf",
                label_visibility="visible",
                key=f"pdf_uploader_{st.session_state.file_uploader_key}"
            )
        with col4:
            # Minimal spacing for precise vertical alignment
            st.markdown("####")  # Using #### for minimal spacing
            process_pdf = st.button(
                "Process PDF",
                disabled=not uploaded_file,
                type="primary",
                use_container_width=True
            )

        # Status message container at the bottom
        status_container = st.empty()

        if uploaded_file and process_pdf:
            file_key = f"pdf_{uploaded_file.name}_{st.session_state.user_id}"
            if file_key not in st.session_state.processed_files:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    # Show processing status
                    status_container.info(f"Processing document: {uploaded_file.name}...")
                    
                    tmp_file.write(uploaded_file.getvalue())
                    text = st.session_state.doc_processor.process_pdf(tmp_file.name)
                    chunks = st.session_state.doc_processor.split_text(text)
                    chunk_embeddings = st.session_state.doc_processor.generate_embeddings(chunks)

                    # Store document and chunks in database
                    doc_id = st.session_state.db.insert_document(
                        title=uploaded_file.name,
                        source='pdf',
                        user_id=st.session_state.user_id
                    )
                    st.session_state.db.insert_chunks(doc_id, chunk_embeddings)
                    st.session_state.processed_files.add(file_key)
                    # Store the new document ID to be used as default selection
                    st.session_state.last_uploaded_doc_id = doc_id
                    
                    # Update status with success message
                    status_container.success(f"✨ Document '{uploaded_file.name}' has been successfully processed and indexed! You can now chat with it.")
                    
                    # Increment the file uploader key to reset it
                    st.session_state.file_uploader_key += 1
                    st.rerun()

    return selected_doc

def main():
    """Main application function."""
    st.title("Chat with Your Documents")

    # Initialize session state
    init_session_state()

    # Setup document interface and get selected document
    selected_doc = setup_document_interface()

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("How can I help you?"):
        if not selected_doc:
            st.error("Please select a document to chat with.")
        else:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            # Get query embedding
            query_embedding = st.session_state.doc_processor.generate_query_embedding(prompt)

            # Search for similar chunks
            similar_chunks = st.session_state.db.search_similar_chunks(
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

            # Display assistant message and generate response
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                response = st.session_state.chatbot.generate_response(
                    query=prompt,
                    context=context,
                    chat_history=st.session_state.chat_history,
                    response_placeholder=response_placeholder
                )

            # Add assistant's message to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Cleanup
    if hasattr(st.session_state, 'db'):
        st.session_state.db.close()

if __name__ == "__main__":
    main()
