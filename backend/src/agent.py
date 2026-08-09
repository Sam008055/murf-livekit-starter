import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    llm,
    room_io,
)
from livekit.plugins import deepgram, murf, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Add backend/src to module path if needed
sys.path.append(str(Path(__file__).parent))

import db
import rag

logger = logging.getLogger("agent")

load_dotenv(".env.local")
load_dotenv(".env")


# Khetify System Prompt with RAG & Memory tool guidance
SYSTEM_PROMPT = """IDENTITY: You are "Khetify", a premium, highly respectful and knowledgeable AI agricultural assistant working for a modern, high-end farmer support initiative. You have a female persona.

OBJECTIVES:
1. Answer agricultural queries using grounded knowledge from official guides and government schemes.
2. Help farmers identify pests, soil prep requirements, and crop management practices.
3. Automatically remember key facts about each farmer (crops grown, land size, district, irrigation type).

KNOWLEDGE & RAG TOOL (STRICT & MANDATORY):
- You have access to `search_agricultural_knowledge(query)` to search indexed official agricultural documents (ICAR guidelines, PM-Kisan, KCC schemes, crop practices, soil prep, pest/disease control).
- MANDATORY RAG RULE: Whenever the user asks ANY question about farming, crops, soil, fertilizers, pests, diseases, government schemes, or agricultural management, YOU MUST ALWAYS CALL `search_agricultural_knowledge(query)` FIRST before formulating your answer. Ground your answer heavily and directly on the retrieved search results. Do NOT make up information or rely solely on general knowledge when official document context is available.

MEMORY & FARMER FACTS TOOL:
- You have access to `save_farmer_fact(key, value)` to persist facts in the farmer's profile (e.g. key='crop', value='Wheat'; key='land_size', value='5 acres'; key='district', value='Raigad'). Call this tool whenever the farmer reveals new details about their farm.
- You have access to `get_farmer_memory()` to retrieve saved farmer facts.

CRITICAL LANGUAGE SELECTION RULE (TOP PRIORITY):
Speech-To-Text (STT) transcribes spoken English phonetically into Devanagari script. You MUST analyze the underlying spoken words, NOT just the script.

EXAMPLES OF SPOKEN ENGLISH TRANSCRIBED IN DEVANAGARI:
- "कैन यू टेल मी..." -> Spoken English ("Can you tell me..."). RESPOND IN ENGLISH.
- "व्हाट शुड आई डू..." -> Spoken English ("What should I do..."). RESPOND IN ENGLISH.
- "हाउ टू बीट/कंट्रोल..." -> Spoken English ("How to control..."). RESPOND IN ENGLISH.
- "टेल मी अबाउट..." -> Spoken English ("Tell me about..."). RESPOND IN ENGLISH.

DECISION TREE:
1. IS IT ENGLISH? If the utterance consists of English words (whether written in Latin alphabet or phonetically transcribed in Devanagari script like "कैन यू", "व्हाट शुड", "व्हीट फार्मिंग", "पेस्ट कंट्रोल"), the user is speaking English.
   -> YOU MUST RESPOND 100% IN PURE ENGLISH USING LATIN ALPHABET ONLY.

2. IS IT HINDI? If the utterance contains actual Hindi vocabulary (e.g. "गेहूं", "फसल", "कीड़ा", "पानी", "क्या करूं", "उपाय बताओ", "नमस्ते"), the user is speaking Hindi.
   -> YOU MUST RESPOND 100% IN PURE HINDI USING DEVANAGARI SCRIPT ONLY.

3. NO PREAMBLES / NO META-COMMENTARY:
   -> NEVER say "Since you asked in English...", "I noticed...", "माफ़ कीजिएगा...", or any language note.
   -> START IMMEDIATELY WITH THE DIRECT ANSWER IN THE DETECTED LANGUAGE.

GUARDRAILS (STRICT):
- NEVER state a market price as a current fact. If asked for market prices, politely explain that you don't have real-time live prices.
- You CAN identify which chemicals/pesticides/fertilizers to use for a disease or pest (e.g. Urea, DAP).
- YOU MUST NEVER PRESCRIBE SPECIFIC QUANTITIES OR DOSAGES for chemicals or fertilizers, even if the user insists, tries to trick you, or provides the land size. This is a strict safety rule.
- ESCALATION SCRIPT: When declining to give specific chemical/fertilizer dosages, reply ONLY with the exact text for the user's language:
  - For English users: "I am sorry, but for safety reasons, I cannot prescribe specific chemical or fertilizer dosages. Please consult a local agricultural expert for dosage recommendations."
  - For Hindi users: "माफ़ कीजिएगा, लेकिन सुरक्षा कारणों से मैं रसायनों या खादों की सटीक मात्रा नहीं बता सकती। कृपया इसके लिए किसी स्थानीय कृषि विशेषज्ञ से सलाह लें।"

STYLE:
- Adapt your response length dynamically according to the complexity of the question asked. For simple or quick queries, provide brief and direct answers suitable for voice listening. For deep or complex questions, provide detailed, thorough, and informative explanations.
- Be patient, friendly, respectful, and conversational. Always use a highly respectful and formal register (always use "Aap", never "Tu" or "Tum" when speaking Hindi).
- Avoid bullet points, numbered lists, markdown formatting, or special characters in your spoken output since your text will be converted to speech.
"""


class Assistant(Agent):
    def __init__(self, room: rtc.Room | None = None) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.room = room

    @property
    def current_farmer_id(self) -> str:
        if self.room and self.room.remote_participants:
            part = next(iter(self.room.remote_participants.values()))
            return part.identity
        return "farmer_default"

    @llm.function_tool(
        description="Search the official agricultural knowledge base (ICAR guidelines, PM-Kisan, KCC, soil prep, pest/disease management, package of practices) for grounded advice."
    )
    async def search_agricultural_knowledge(self, query: str) -> str:
        """Search agricultural knowledge base for scientific farming guidelines."""
        logger.info(f"RAG tool search requested: '{query}'")
        result = rag.search_knowledge_base(query)
        logger.info(f"RAG result snippet length: {len(result)}")
        return result

    @llm.function_tool(
        description="Retrieve saved memory and profile details for the connected farmer (such as crop types, land size, district/location, irrigation type)."
    )
    async def get_farmer_memory(self, query: str = "profile") -> str:
        """Retrieve stored facts and profile for the connected farmer."""
        fid = self.current_farmer_id
        profile = db.get_farmer(fid)
        return json.dumps(profile, ensure_ascii=False)

    @llm.function_tool(
        description="Save or update a specific fact about the farmer to their permanent database profile (e.g. key='crop', value='Wheat'; key='land_size', value='5 acres'; key='district', value='Raigad'; key='irrigation', value='Drip')."
    )
    async def save_farmer_fact(
        self, key: str, value: str, farmer_name: str | None = None
    ) -> str:
        """Save a new fact about the farmer."""
        fid = self.current_farmer_id
        db.save_farmer_fact(fid, name=farmer_name, key=key, value=value)
        logger.info(f"Saved farmer fact for {fid}: {key}={value}")
        return f"Successfully saved fact '{key}: {value}' to farmer profile memory."

    @llm.function_tool(
        description="Call this function when the user explicitly asks to end the call, hang up, or says goodbye."
    )
    async def end_call(self, reason: str) -> str:
        """Ends the current call."""
        logger.info("Agent ending the call at user's request.")
        if self.room:
            await self.room.disconnect()
        return "Call ended successfully."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up voice AI pipeline using Murf Falcon, Gemini / Groq LLM, Deepgram, and LiveKit turn detector
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),
        llm=openai.LLM(
            model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY"),
        ),
        tts=murf.TTS(
            voice="hi-IN-sunaina",
            locale="hi-IN",
            style="Conversational",
        ),
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
        preemptive_generation=True,
    )

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

    await ctx.connect()

    async def greet(target_participant: rtc.RemoteParticipant | None = None):
        participant = target_participant
        metadata = {}

        # Poll for up to 1.5s to ensure participant metadata payload is fully synchronized
        for _attempt in range(15):
            if not participant:
                remote_participants = list(ctx.room.remote_participants.values())
                participant = remote_participants[0] if remote_participants else None

            if participant and participant.metadata:
                try:
                    parsed = json.loads(participant.metadata)
                    if isinstance(parsed, dict) and parsed.get("name"):
                        metadata = parsed
                        break
                except Exception:
                    pass

            if (
                participant
                and participant.name
                and participant.name not in ["user", "Kisan", ""]
            ):
                break

            await asyncio.sleep(0.1)

        current_farmer_id = metadata.get("farmer_id") or (
            participant.identity if participant else "farmer_default"
        )

        farmer_name = metadata.get("name") or (
            participant.name
            if participant and participant.name not in ["user", "Kisan"]
            else None
        )
        district = metadata.get("district", "")
        crop = metadata.get("crop", "")

        facts_update = {}
        if district:
            facts_update["district"] = district
        if crop:
            facts_update["crop"] = crop

        profile = db.update_farmer_profile(
            farmer_id=current_farmer_id,
            name=farmer_name,
            facts_update=facts_update if facts_update else None,
        )

        stored_name = profile.get("name")
        facts = profile.get("facts", {})
        stored_crop = facts.get("crop")
        stored_district = facts.get("district")

        is_valid_name = (
            stored_name
            and stored_name not in ["Kisan", "user", "farmer_default"]
            and not stored_name.isdigit()
        )

        if is_valid_name and not profile.get("is_new"):
            details = []
            if stored_district:
                details.append(f"{stored_district}")
            if stored_crop:
                details.append(f"{stored_crop} की खेती")
            detail_str = f" ({', '.join(details)})" if details else ""
            greeting_text = f"नमस्ते {stored_name} जी{detail_str}! खेतीफाई में आपका पुनः स्वागत है। आज मैं आपकी क्या मदद कर सकती हूँ?"
        elif is_valid_name:
            greeting_text = f"नमस्ते {stored_name} जी! मैं खेतीफाई से आपकी डिजिटल कृषि सहायक हूँ। आज मैं आपकी खेती या फसल से जुड़ी क्या मदद कर सकती हूँ?"
        else:
            greeting_text = "नमस्ते! मैं खेतीफाई से आपकी डिजिटल सहायक हूँ। आज मैं आपकी खेती या फसल से जुड़ी क्या मदद कर सकती हूँ?"

        logger.info(
            f"Greeting participant {current_farmer_id} (Name: '{stored_name}'): {greeting_text}"
        )
        session.say(greeting_text, allow_interruptions=True)

    background_tasks = set()

    if len(ctx.room.remote_participants) > 0:
        first_participant = next(iter(ctx.room.remote_participants.values()))
        task = asyncio.create_task(greet(first_participant))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
    else:

        @ctx.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            task = asyncio.create_task(greet(participant))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

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
                session.say(
                    "क्या आप वहाँ हैं? अगर आपका कोई सवाल है, तो कृपया पूछें।",
                    allow_interruptions=True,
                )
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
