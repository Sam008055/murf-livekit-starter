import os
import asyncio
from dotenv import load_dotenv
from livekit.agents import llm
from livekit.plugins import google

load_dotenv(".env", override=True)


async def main():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    print(
        f"Testing Google Gemini LLM with key ending in ...{api_key[-4:] if api_key else 'None'}"
    )

    for model_name in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
        try:
            print(f"\n--- Testing {model_name} ---")
            llm_inst = google.LLM(model=model_name, api_key=api_key)
            chat_ctx = llm.ChatContext()
            chat_ctx.add_message(
                role="user", content="Say hello in one short sentence."
            )

            stream = llm_inst.chat(chat_ctx=chat_ctx)
            text_out = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    text_out += chunk.choices[0].delta.content
            print(f"[OK] {model_name} response: {text_out.strip()}")
        except Exception as e:
            print(f"[FAILED] {model_name}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
