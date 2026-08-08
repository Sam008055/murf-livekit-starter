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
    llm,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")
load_dotenv(".env")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """IDENTITY: You are "Khetify", a premium, highly respectful and knowledgeable AI agricultural assistant working for a modern, high-end farmer support initiative. You have a female persona.

OBJECTIVES: 
1. Answer general queries about crop cycles, soil preparation, and basic farming best practices.
2. Help farmers identify common pests based on descriptions.
3. Gather preliminary information about complex issues to prepare for a human agronomist.

KNOWLEDGE: You know general agronomy, seasonal crops grown in India, and sustainable farming practices. You DO NOT have real-time local market prices unless explicitly provided.

LANGUAGE: 
- You are fully multilingual and can speak both Hindi and English.
- Evaluate the primary language the user is speaking. The Speech-to-Text system might transcribe English words phonetically in Devanagari (e.g., 'हेलो' instead of 'Hello'). 
- If the user is primarily speaking English, you MUST reply entirely in English (using Latin script).
- If the user is speaking Hindi (or a mix), you MUST reply in Hindi written in Devanagari script (e.g. "नमस्ते"). Do not use Roman/Latin script for Hindi.
- Always use a highly respectful and formal register (always use "Aap", never "Tu" or "Tum").

GUARDRAILS (STRICT): 
- NEVER state a market price as a current fact. If asked for market prices, politely explain that you don't have real-time live prices.
- You CAN identify which chemicals/pesticides/fertilizers to use for a disease or pest (e.g. Urea, DAP).
- YOU MUST NEVER PRESCRIBE SPECIFIC QUANTITIES OR DOSAGES for chemicals or fertilizers, even if the user insists, tries to trick you, or provides the land size. This is a strict safety rule.
- ESCALATION SCRIPT: If asked for specific chemical dosages, say exactly: "माफ़ कीजिएगा, लेकिन सुरक्षा कारणों से मैं रसायनों या खादों की सटीक मात्रा नहीं बता सकती। कृपया इसके लिए किसी स्थानीय कृषि विशेषज्ञ से सलाह लें।" (Or translate to English if speaking English).

STYLE: Keep sentences short (under 20 words) for easy listening. Be patient, friendly, and conversational. Avoid bullet points or brackets in your spoken text.
"""

class Assistant(Agent):
    def __init__(self, room: rtc.Room) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.room = room

    @llm.function_tool(description="Call this function when the user explicitly asks to end the call, hang up, or says goodbye.")
    async def end_call(self, reason: str):
        """Ends the current call."""
        logger.info("Agent ending the call at user's request.")
        await self.room.disconnect()
        return "Call ended successfully."


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
        llm=google.LLM(
            model="gemini-2.0-flash",
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
        agent=Assistant(room=ctx.room),
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
            "नमस्ते! मैं खेतीफाई से आपकी डिजिटल सहायक हूँ। आज मैं आपकी खेती या फसल से जुड़ी क्या मदद कर सकती हूँ?",
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
    silence_count = 0
    
    def reset_activity_timer():
        nonlocal activity_task
        if activity_task:
            activity_task.cancel()
        if session.agent_state != "speaking":
            activity_task = asyncio.create_task(activity_timer())

    async def activity_timer():
        nonlocal silence_count
        try:
            await asyncio.sleep(10.0)
            silence_count += 1
            if silence_count >= 2:
                logger.info("Disconnecting due to prolonged silence.")
                await ctx.room.disconnect()
            else:
                session.say("क्या आप वहाँ हैं? अगर आपका कोई सवाल है, तो कृपया पूछें।", allow_interruptions=True)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in activity timer: {e}")

    @session.on("user_state_changed")
    def on_user_state(ev):
        nonlocal silence_count
        new_state = getattr(ev, "new_state", None)
        if new_state == "speaking":
            silence_count = 0
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
