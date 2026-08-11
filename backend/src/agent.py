import asyncio
import json
import logging
import os
import sys
import datetime
import urllib.parse
import requests
from bs4 import BeautifulSoup
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
    tokenize,
)
from livekit.plugins import deepgram, murf, noise_cancellation, openai, silero, google
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Add backend/src to module path if needed
sys.path.append(str(Path(__file__).parent))

import db
import rag

# Ensure latest environment variables from .env.local / .env override cached environment
load_dotenv(".env.local", override=True)
load_dotenv(".env", override=True)

logger = logging.getLogger("agent")


# Khetify System Prompt with RAG & Memory tool guidance
SYSTEM_PROMPT = """IDENTITY: You are "Khetify", a premium, highly respectful and knowledgeable AI agricultural assistant working for a modern, high-end farmer support initiative. You have a female persona.

OBJECTIVES:
1. Answer agricultural queries using grounded knowledge from official guides and government schemes.
2. Help farmers identify pests, soil prep requirements, and crop management practices.
3. Automatically remember key facts about each farmer (crops grown, land size, district, irrigation type).

KNOWLEDGE & RAG TOOL (STRICT & MANDATORY):
- You have access to `search_agricultural_knowledge(query)` to search indexed official agricultural documents (ICAR guidelines, PM-Kisan, KCC schemes, crop practices, soil prep, pest/disease control).
- MANDATORY RAG RULE: Whenever the user asks ANY question about farming, crops, soil, fertilizers, pests, diseases, government schemes, or agricultural management, YOU MUST ALWAYS CALL `search_agricultural_knowledge(query)` FIRST before formulating your answer. Ground your answer heavily and directly on the retrieved search results. Do NOT make up information or rely solely on general knowledge when official document context is available.
- RAG LANGUAGE TRANSLATION RULE: The retrieved search results may contain text in Hindi or English. YOU MUST ALWAYS RESPOND IN THE USER'S DETECTED LANGUAGE, NOT THE LANGUAGE OF THE RETRIEVED TEXT. If the user spoke in English (e.g. "Can you tell me more benefits..."), you MUST translate and present the retrieved RAG facts 100% in English. If the user spoke in Hindi, present the facts 100% in Hindi.

MEMORY & FARMER FACTS TOOL:
- You have access to `save_farmer_fact(key, value)` to persist facts in the farmer's profile (e.g. key='crop', value='Wheat'; key='land_size', value='5 acres'; key='district', value='Raigad'). 
- MANDATORY CONSENT RULE: Before you save any new fact about the farmer, you MUST explicitly ask for their permission to remember it. For example: "May I remember that you grow Wheat to help you better next time?" If they say no, DO NOT save it. If they agree, call `save_farmer_fact`.
- You have access to `get_farmer_memory()` to retrieve saved farmer facts.

MARKET PRICE & WEATHER TOOLS:
- You have access to `get_market_price(crop_name, district, state)` to fetch real-time market prices from agricultural data sources.
- You have access to `get_weather(location)` to get current weather conditions and forecasts for a district or city.
- Whenever a user asks for prices, weather, or forecasts, first use `get_farmer_memory()` to check if you know their district/state. If you don't know it, ask them for their location.
- After fetching data, clearly state the source or date if available, so the farmer knows it is real data. If no data is found, politely apologize.

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

3. TOOL EXECUTION AND SPEECH RULES:
   -> When you need to use a tool, invoke it directly using the API. DO NOT speak, type, or output the tool name, JSON, `<function>` tags, or queries in your text response.
   -> DO NOT say "Let me check", "I am searching", or "Query:".
   -> Wait for the tool to return results, then speak ONLY the final answer directly to the user.
   -> NEVER explain your language choice (e.g., do not say "Since you asked in English..."). Just speak the language natively.

GUARDRAILS (STRICT):
- You CAN identify which chemicals/pesticides/fertilizers to use for a disease or pest (e.g. Urea, DAP).
- YOU MUST NEVER PRESCRIBE SPECIFIC QUANTITIES OR DOSAGES for chemicals or fertilizers, even if the user insists, tries to trick you, or provides the land size. This is a strict safety rule.
- SAFETY MANDATE RESPONSE: When declining to give specific chemical/fertilizer dosages, reply ONLY with the exact text for the user's language:
  - For English users: "I am sorry, but for safety reasons, I cannot prescribe specific chemical or fertilizer dosages. Please consult a local agricultural expert for dosage recommendations."
  - For Hindi users: "माफ़ कीजिएगा, लेकिन सुरक्षा कारणों से मैं रसायनों या खादों की सटीक मात्रा नहीं बता सकती। कृपया इसके लिए किसी स्थानीय कृषि विशेषज्ञ से सलाह लें।"

STYLE:
- Adapt your response length dynamically according to the complexity of the question asked. For simple or quick queries, provide brief and direct answers suitable for voice listening. For deep or complex questions, provide detailed, thorough, and informative explanations.
- Be patient, friendly, respectful, and conversational. Always use a highly respectful and formal register (always use "Aap", never "Tu" or "Tum" when speaking Hindi).
- Avoid bullet points, numbered lists, markdown formatting, brackets or parentheses like (), or special characters in your spoken output since your text will be converted to speech.
"""


class Assistant(Agent):
    def __init__(self, room: rtc.Room | None = None) -> None:
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        prompt = SYSTEM_PROMPT + f"\n\nCURRENT DATE & TIME:\nToday is {today}. Use this to understand relative time like 'yesterday' or 'today'."
        super().__init__(instructions=prompt)
        self.room = room

    @property
    def current_farmer_id(self) -> str:
        if self.room and self.room.remote_participants:
            part = next(iter(self.room.remote_participants.values()))
            if part.metadata:
                try:
                    parsed = json.loads(part.metadata)
                    if isinstance(parsed, dict):
                        if parsed.get("farmer_id"):
                            return parsed["farmer_id"]
                        if parsed.get("name"):
                            return f"farmer_{parsed['name'].strip().lower().replace(' ', '_')}"
                except Exception:
                    pass
            if part.name and part.name not in ["user", "Kisan", ""]:
                return f"farmer_{part.name.strip().lower().replace(' ', '_')}"
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
        description="Fetch real-time agricultural market prices (mandi bhav) for a specific crop in a given district and state."
    )
    async def get_market_price(
        self, crop_name: str, district: str = "", state: str = ""
    ) -> str:
        """Fetch real-time market prices using a web search."""
        query = f"{crop_name} price"
        if district:
            query += f" in {district}"
        if state:
            query += f" {state}"
        query += " mandi today"
        
        logger.info(f"Market price search requested: '{query}'")
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=3)]
                
            if not results:
                return f"No recent market price data found for {crop_name} in {district}. Tell the farmer you couldn't find the latest data."
                
            snippets = "\n".join([r['body'] for r in results])
            return f"Here is the latest market data found:\n{snippets}\n\nExtract the price and inform the farmer in their language."
        except Exception as e:
            logger.error(f"Error fetching market price: {e}")
            return "An error occurred while fetching market data. Please politely apologize to the farmer."

    @llm.function_tool(
        description="Fetch current weather conditions and forecast for a specific district or city."
    )
    async def get_weather(self, location: str) -> str:
        """Fetch real-time weather using wttr.in API."""
        logger.info(f"Weather requested for: '{location}'")
        try:
            url = f"https://wttr.in/{urllib.parse.quote(location)}?format=j1"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return "Failed to fetch weather data. Please politely apologize to the farmer."
            
            data = response.json()
            current = data['current_condition'][0]
            temp_c = current['temp_C']
            feels_like = current['FeelsLikeC']
            humidity = current['humidity']
            desc = current['weatherDesc'][0]['value']
            
            today = data['weather'][0]
            max_temp = today['maxtempC']
            min_temp = today['mintempC']
            chance_of_rain = today['hourly'][0]['chanceofrain']
            
            weather_report = (
                f"Current Weather in {location}: {desc}, {temp_c}°C (Feels like {feels_like}°C). "
                f"Humidity: {humidity}%. "
                f"Today's Forecast: High {max_temp}°C, Low {min_temp}°C. "
                f"Rain chance: {chance_of_rain}%."
            )
            return weather_report
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return "An error occurred while fetching weather data. Please politely apologize to the farmer."

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

    groq_key = os.getenv("GROQ_API_KEY") or ""
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    key_suffix = f"...{groq_key[-4:]}" if len(groq_key) >= 4 else "NOT SET"
    logger.info(
        f"Starting agent for room '{ctx.room.name}' using Groq model '{groq_model}' and API key ending in {key_suffix}"
    )

    # Set up voice AI pipeline using Murf, Gemini LLM, Deepgram, and LiveKit turn detector
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        tts=murf.TTS(
            voice="Anisha",  # do not hardcode the locale key
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
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

        # For SIP participants, wait until their audio track is subscribed (meaning they picked up)
        if participant and participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            logger.info("Waiting for SIP participant to answer (audio track subscribed)...")
            
            def has_subscribed_audio_track():
                for pub in participant.track_publications.values():
                    if pub.kind == rtc.TrackKind.KIND_AUDIO and pub.subscribed:
                        return True
                return False

            # Wait up to 60 seconds for the user to answer
            for _ in range(600):
                if has_subscribed_audio_track():
                    logger.info("SIP participant answered the call.")
                    # Add a small delay after pickup for a more natural feel
                    await asyncio.sleep(1.0)
                    break
                await asyncio.sleep(0.1)

        farmer_name = metadata.get("name") or (
            participant.name
            if participant and participant.name not in ["user", "Kisan"]
            else None
        )

        raw_fid = metadata.get("farmer_id") or (
            participant.identity if participant else "farmer_default"
        )
        if farmer_name and (
            not metadata.get("farmer_id") or raw_fid in ["farmer_default", "user"]
        ):
            slug_name = farmer_name.strip().lower().replace(" ", "_")
            current_farmer_id = f"farmer_{slug_name}"
        else:
            current_farmer_id = raw_fid

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
        is_returning = profile.get("is_returning", False)

        is_valid_name = (
            stored_name
            and stored_name not in ["Kisan", "user", "farmer_default"]
            and not stored_name.isdigit()
        )

        if ctx.room.name == "outbound-emergency":
            # Data-driven emergency alert greeting
            greeting_text = "नमस्ते! मैं खेतीफाई से बोल रही हूँ। यह एक महत्वपूर्ण अलर्ट है। करनाल में अभी भारी बारिश और तूफान की चेतावनी है, और बासमती धान का मंडी भाव ३,३५५ रुपये प्रति क्विंटल चल रहा है। मौसम खराब होने से पहले, क्या आप अपनी फसल सुरक्षित करने या मंडी में बेचने के बारे में कोई जानकारी चाहते हैं?"
        else:
            if is_valid_name and is_returning:
                if stored_district and stored_crop:
                    greeting_text = f"नमस्ते {stored_name} जी! {stored_district} में {stored_crop} की खेती के लिए खेतीफाई में आपका पुनः स्वागत है। आज मैं आपकी क्या मदद कर सकती हूँ?"
                elif stored_district:
                    greeting_text = f"नमस्ते {stored_name} जी! {stored_district} से खेतीफाई में आपका पुनः स्वागत है। आज मैं आपकी क्या मदद कर सकती हूँ?"
                elif stored_crop:
                    greeting_text = f"नमस्ते {stored_name} जी! {stored_crop} की खेती के लिए खेतीफाई में आपका पुनः स्वागत है। आज मैं आपकी क्या मदद कर सकती हूँ?"
                else:
                    greeting_text = f"नमस्ते {stored_name} जी! खेतीफाई में आपका पुनः स्वागत है। आज मैं आपकी क्या मदद कर सकती हूँ?"
            elif is_valid_name:
                greeting_text = f"नमस्ते {stored_name} जी! मैं खेतीफाई से आपकी डिजिटल कृषि सहायक हूँ। आज मैं आपकी खेती या फसल से जुड़ी क्या मदद कर सकती हूँ?"
            else:
                greeting_text = "नमस्ते! मैं खेतीफाई से आपकी डिजिटल कृषि सहायक हूँ। आज मैं आपकी खेती या फसल से जुड़ी क्या मदद कर सकती हूँ?"

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


    @session.on("agent_speech_committed")
    def on_agent_speech_committed(msg):
        # Truncate history to prevent token limits on long calls
        try:
            if hasattr(session, "history") and hasattr(session.history, "_items"):
                # Keep system prompt (index 0) and last 14 messages (sliding window of 15)
                if len(session.history._items) > 15:
                    session.history._items = [
                        session.history._items[0]
                    ] + session.history._items[-14:]
                    logger.info(
                        f"Truncated conversation history to {len(session.history._items)} items to save tokens."
                    )
        except Exception as e:
            logger.warning(f"Failed to truncate history: {e}")

    reset_activity_timer()


if __name__ == "__main__":
    cli.run_app(server)
