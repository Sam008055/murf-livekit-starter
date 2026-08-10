import os
import logging
from pinecone import Pinecone
from pinecone_plugins.assistant.models.chat import Message
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("rag")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

def search_knowledge_base(query: str, top_k: int = 2) -> str:
    """
    Search agricultural knowledge base using Pinecone Assistant.
    """
    if not PINECONE_API_KEY:
        return "Pinecone API key is not configured. Please ask general guidance for now."

    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        assistant = pc.assistant.Assistant(assistant_name="murfai")
        msg = Message(content=query)
        resp = assistant.chat(messages=[msg])
        
        answer = resp["message"]["content"]
        if not answer:
            return "No specific agricultural guidelines found in document knowledge base for this exact phrase."
        return answer
    except Exception as e:
        logger.error(f"Pinecone Assistant error: {e}")
        return f"Error retrieving knowledge: {e}"
