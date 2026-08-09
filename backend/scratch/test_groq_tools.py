import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.append("src")

load_dotenv(".env.local")
load_dotenv(".env")

from livekit.plugins import openai
from livekit.agents import llm
from agent import Assistant

async def test(strict: bool):
    print(f"\n================ Testing _strict_tool_schema={strict} ================")
    tools = [m.__get__(object()) for m in Assistant.__dict__.values() if isinstance(m, llm.FunctionTool)]
    
    l = openai.LLM(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY"),
        _strict_tool_schema=strict,
    )
    
    ctx = llm.ChatContext()
    ctx.add_message(
        role="user",
        content="कैन यू टेल मी हाउ टू कंट्रोल व्हीट रस्ट?"
    )
    
    try:
        stream = l.chat(chat_ctx=ctx, tools=tools)
        async for chunk in stream:
            if chunk.delta:
                if chunk.delta.content:
                    print(chunk.delta.content, end="", flush=True)
                if chunk.delta.tool_calls:
                    print("\n[TOOL CALL]:", chunk.delta.tool_calls)
        print("\nSUCCESS!")
    except Exception as e:
        print("\nERROR:", type(e), e)

async def main():
    await test(True)
    await test(False)

if __name__ == "__main__":
    asyncio.run(main())
