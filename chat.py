import os
from typing import List
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

class ChatBot:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0.7,
            streaming=True
        )

    def generate_response(self, query: str, context: List[str], chat_history: List[dict], response_placeholder) -> str:
        # Prepare the system message with context
        context_text = "\n\n".join(context)
        system_message = SystemMessage(content=f"""You are a knowledgeable AI assistant focused on providing detailed and well-structured responses.
        
        Guidelines for your responses:
        - Provide comprehensive and detailed answers
        - Use bullet points to break down complex information
        - Include specific examples or references from the documents when relevant
        - Structure your response in a clear, organized manner
        - If multiple points are related, use sub-bullets to show the relationship
        - When explaining concepts, break them down into digestible parts
        - If you cannot answer based on the context, clearly state that
        
        Use the following context to answer the user's questions:
        
        Context:
        {context_text}""")

        # Prepare the chat history
        messages = [system_message]
        for message in chat_history:
            if message["role"] == "user":
                messages.append(HumanMessage(content=message["content"]))
            else:
                messages.append(AIMessage(content=message["content"]))

        # Add the current query
        messages.append(HumanMessage(content=query))

        # Generate streaming response
        response_text = ""
        for chunk in self.llm.stream(messages):
            if chunk.content:
                response_text += chunk.content
                response_placeholder.markdown(response_text + "▌")
        
        # Update placeholder one final time without cursor
        response_placeholder.markdown(response_text)
        return response_text
