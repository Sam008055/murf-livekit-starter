from livekit.agents.llm import ChatContext, ChatMessage

ctx = ChatContext()
ctx.messages.append(ChatMessage(role="user", content="hello"))

print("Using .messages.append")
print("content:", ctx.messages[-1].content)

# In livekit agents, ChatContext might use append()
ctx2 = ChatContext()
try:
    ctx2.append(text="hello", role="user")
    print("Using .append()")
    print("items type:", type(ctx2.messages))

    # Try modifying
    if hasattr(ctx2, "messages") and isinstance(ctx2.messages, list):
        msg = ctx2.messages[-1]
        msg.content = msg.content + " [modified]"
        print("modified content:", msg.content)
except Exception as e:
    print("Error:", e)
