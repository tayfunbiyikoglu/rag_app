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
        )

    def generate_response(self, query: str, context: List[str], chat_history: List[dict]) -> str:
        # Prepare the system message with context
        context_text = "\n\n".join(context)
        system_message = SystemMessage(content=f"""You are a helpful AI assistant. Use the following context to answer the user's questions.
        If you cannot answer the question based on the context, say so.
        
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

        # Generate response
        response = self.llm.predict_messages(messages)
        return response.content
