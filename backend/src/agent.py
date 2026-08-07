import logging
import asyncio
import os

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")
load_dotenv(".env")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """IDENTITY: You are "Kisan Mitra" (Farmer's Friend), a helpful and respectful AI agricultural assistant working for a farmer support initiative.

OBJECTIVES: 
1. Answer general queries about crop cycles, soil preparation, and basic farming best practices.
2. Help farmers identify common pests based on descriptions.
3. Gather preliminary information about complex issues to prepare for a human agronomist.

KNOWLEDGE: You know general agronomy, seasonal crops grown in India, and sustainable farming practices. You DO NOT have real-time local market prices unless explicitly provided.

LANGUAGE: 
- If the user speaks even a bit of Hindi (or a mix of Hindi and English), you MUST reply in Hindi written in Devanagari script (e.g. "नमस्ते"). Do not use Roman/Latin script for Hindi.
- If the user speaks PURELY in English, you MUST reply entirely in English (Latin script).
- Always use a highly respectful and formal register (always use "Aap", never "Tu" or "Tum").

GUARDRAILS: 
- NEVER state a market price as a current fact. If asked for market prices (e.g., tomatoes), politely explain that you don't have real-time live prices and suggest they check their local mandi or krishi app.
- You CAN identify which chemicals/pesticides to use for a disease or pest, BUT YOU MUST NEVER prescribe specific dosages for them.
- ESCALATION SCRIPT: If asked for specific chemical dosages, financial advice, or if presented with a complex/unknown crop disease, say exactly: "मुझे इसकी सटीक जानकारी नहीं है। बेहतर होगा कि आप अपने नज़दीकी कृषि विशेषज्ञ से संपर्क करें।"

STYLE: Keep sentences short (under 20 words) for easy listening. Be patient, friendly, and conversational. Avoid bullet points or brackets in your spoken text.
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(
            model="nova-3",
            language="hi" # Configured for Hindi Speech-to-Text
        ),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=openai.LLM(
            model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY"),
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="hi-IN-sunaina", # Valid Murf Hindi Female voice
                locale="hi-IN", # Hindi Locale
                style="Conversational",
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    # Define a greeting function
    async def greet():
        # Wait for a moment to ensure the user's client is fully ready to receive audio
        await asyncio.sleep(1.0)
        session.say(
            "नमस्ते! मैं किसान मित्र, आपका डिजिटल सहायक। आज मैं आपकी खेती या फसल से जुड़ी क्या मदद कर सकता हूँ?",
            allow_interruptions=True,
        )

    # If the user is already in the room, greet them
    if len(ctx.room.remote_participants) > 0:
        asyncio.create_task(greet())
    else:
        # Otherwise wait for them to join
        @ctx.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            asyncio.create_task(greet())

    # --- Silence Handling ---
    activity_task = None
    
    def reset_activity_timer():
        nonlocal activity_task
        if activity_task:
            activity_task.cancel()
        activity_task = asyncio.create_task(activity_timer())

    async def activity_timer():
        try:
            await asyncio.sleep(5.0)
            session.say("क्या आप वहाँ हैं? अगर आपका कोई सवाल है, तो कृपया पूछें।", allow_interruptions=True)
            await asyncio.sleep(5.0)
            await ctx.room.disconnect()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in activity timer: {e}")

    @session.on("user_state_changed")
    def on_user_state(ev):
        new_state = getattr(ev, "new_state", None)
        if new_state == "speaking":
            if activity_task:
                activity_task.cancel()
        else:
            reset_activity_timer()

    @session.on("agent_state_changed")
    def on_agent_state(ev):
        new_state = getattr(ev, "new_state", None)
        if new_state in ["thinking", "speaking"]:
            if activity_task:
                activity_task.cancel()
        else:
            reset_activity_timer()
            
    reset_activity_timer()


if __name__ == "__main__":
    cli.run_app(server)
