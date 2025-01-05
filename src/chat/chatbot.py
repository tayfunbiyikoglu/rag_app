"""Chatbot implementation using Azure OpenAI."""
from typing import List, Dict
import streamlit as st
from langchain_community.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import os
import logging

logger = logging.getLogger(__name__)

class ChatBot:
    def __init__(self):
        """Initialize the chatbot with Azure OpenAI."""
        self.chat = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            openai_api_type="azure",
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0.7,
        )

    def generate_response(
        self,
        query: str,
        context: List[str],
        chat_history: List[Dict],
        response_placeholder: st.empty
    ) -> str:
        """Generate a response based on the query and context."""
        try:
            # Create system message with context
            system_content = """You are a helpful AI assistant that answers questions based on the provided document context.
            Always be accurate and use information only from the provided context.
            If you're not sure about something, say so.

            Guidelines for your responses:
            - Provide comprehensive and detailed answers
            - Use bullet points to break down complex information
            - Include specific examples or references from the documents when relevant
            - Structure your response in a clear, organized manner
            - If multiple points are related, use sub-bullets to show the relationship
            - When explaining concepts, break them down into digestible parts
            - If you cannot answer based on the context, clearly state that

            """

            if context:
                system_content += "\n\nRelevant context from documents:\n" + "\n".join(context)

            messages = [SystemMessage(content=system_content)]

            # Add chat history
            for msg in chat_history[:-1]:  # Exclude the latest user message
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

            # Add the current query
            messages.append(HumanMessage(content=query))

            # Stream the response
            response_text = ""
            for chunk in self.chat.stream(messages):
                if chunk.content:
                    response_text += chunk.content
                    response_placeholder.markdown(response_text + "▌")

            # Update placeholder with final response
            response_placeholder.markdown(response_text)
            return response_text

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            response_placeholder.error(error_msg)
            return error_msg
