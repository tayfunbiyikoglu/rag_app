import streamlit as st
from database import Database
from document_processor import DocumentProcessor
from chat import ChatBot
import tempfile
from typing import List, Tuple

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Initialize components
db = Database()
doc_processor = DocumentProcessor()
chatbot = ChatBot()

st.title("RAG Application")

# Sidebar for admin interface
with st.sidebar:
    st.header("Admin Interface")
    upload_option = st.radio("Choose upload method:", ["PDF File", "URL"])
    
    if upload_option == "PDF File":
        uploaded_file = st.file_uploader("Upload PDF", type="pdf")
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                text = doc_processor.process_pdf(tmp_file.name)
                st.success("PDF processed successfully!")
    else:
        url = st.text_input("Enter URL:")
        if url and st.button("Process URL"):
            text = doc_processor.process_url(url)
            st.success("URL processed successfully!")

    if "text" in locals():
        with st.spinner("Processing document..."):
            # Split text into chunks
            chunks = doc_processor.split_text(text)
            
            # Generate embeddings
            chunk_embeddings = doc_processor.generate_embeddings(chunks)
            
            # Store in database
            doc_title = uploaded_file.name if upload_option == "PDF File" else url
            doc_source = "PDF" if upload_option == "PDF File" else "URL"
            doc_id = db.insert_document(doc_title, doc_source)
            db.insert_chunks(doc_id, chunk_embeddings)
            
            st.success("Document processed and stored in the database!")

# Main chat interface
st.header("Chat Interface")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents"):
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)

    # Generate embedding for the query
    query_embedding = doc_processor.generate_query_embedding(prompt)
    
    # Retrieve relevant chunks
    similar_chunks = db.search_similar_chunks(query_embedding)
    context = [chunk[0] for chunk in similar_chunks]
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chatbot.generate_response(prompt, context, st.session_state.chat_history)
            st.write(response)
            
            # Add assistant message to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})

# Cleanup
db.close()
