import asyncio
import os

from dotenv import load_dotenv
from livekit.plugins import google, openai

load_dotenv(".env", override=True)


async def test_google_llm():
    print("\n--- Testing Google Gemini LLM ---")
    try:
        llm_inst = google.LLM(
            model="gemini-2.0-flash-exp",
            api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
        )
        print("Google LLM initialized successfully.")
    except Exception as e:
        print(f"Google LLM Error: {e}")


async def test_groq_llm():
    print("\n--- Testing Groq LLM via openai.LLM ---")
    try:
        llm_inst = openai.LLM(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
            _strict_tool_schema=False,
        )
        print("Groq LLM initialized successfully.")
    except Exception as e:
        print(f"Groq LLM Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_google_llm())
    asyncio.run(test_groq_llm())
