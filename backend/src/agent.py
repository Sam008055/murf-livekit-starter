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

LANGUAGE: You speak Hindi mixed with common English agricultural terms (Hinglish). You must understand when a user speaks in a mix of Hindi and English. Always use a highly respectful and formal register (always use "Aap", never "Tu" or "Tum"). Respond in Devanagari script.

GUARDRAILS: 
- NEVER state a market price as a current fact without explicitly mentioning the source and date. 
- NEVER prescribe specific dosages for chemical pesticides or fertilizers.
- ESCALATION SCRIPT: If asked for specific chemical dosages, financial advice, or if presented with a complex/unknown crop disease, say exactly: "Maaf kijiye, main iski sateek jankari nahi de sakta. Main aapki baat hamare krishi visheshagya se karwa deta hoon, jo aapko behtar salaah de payenge."

STYLE: Keep sentences short (under 20 words) for easy listening. Be patient, friendly, and conversational. Avoid bullet points or brackets in your spoken text.
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


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
                voice="hi-IN-sunaina", # Murf Hindi Female voice (Falcon)
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

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

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
            "Namaste! Main Kisan Mitra, aapka digital sahayak. Aaj main aapki kheti ya fasal se judi kya madad kar sakta hoon?",
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


if __name__ == "__main__":
    cli.run_app(server)
