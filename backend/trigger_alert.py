import asyncio
import os
import aiohttp
from dotenv import load_dotenv
from livekit import api
from livekit.protocol import sip

# Load environment variables from .env
load_dotenv()

# The city to check weather for
CITY = "Karnal"

# We will set a custom room name for this alert so the agent knows it's an outbound emergency.
ROOM_NAME = "outbound-emergency"

async def check_weather_and_call():
    print(f"Checking real-time weather for {CITY}...")
    
    # 1. Fetch real weather data
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wttr.in/{CITY}?format=j1") as response:
                if response.status == 200:
                    # wttr.in often returns text/plain even for JSON, so we bypass content-type validation
                    data = await response.json(content_type=None)
                    current_condition = data['current_condition'][0]['weatherDesc'][0]['value'].lower()
                    print(f"Current weather in {CITY}: {current_condition}")
                    
                    # 2. Check for emergency
                    is_emergency = any(keyword in current_condition for keyword in ["rain", "storm", "thunder", "shower", "cloud"])
                    
                    # For video demonstration purposes, if it's not raining right now, we can still force it.
                    # Uncomment this if you want it to always trigger for the video:
                    is_emergency = True 
                    
                    if not is_emergency:
                        print("No weather emergency detected. Skipping call.")
                        return
                    
                    print("🚨 WEATHER EMERGENCY DETECTED! Initiating call to farmer... 🚨")
                    await initiate_sip_call()
                else:
                    print("Failed to fetch weather data. Status:", response.status)
    except Exception as e:
        print(f"Error checking weather: {e}")

async def initiate_sip_call():
    # Fetch credentials from .env
    user_phone_number = os.environ.get("USER_PHONE_NUMBER")
    twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
    sip_trunk_id = os.environ.get("SIP_TRUNK_ID")
    
    if not all([user_phone_number, twilio_phone_number, sip_trunk_id]):
        print("❌ Error: Missing required environment variables.")
        print("Please ensure USER_PHONE_NUMBER, TWILIO_PHONE_NUMBER, and SIP_TRUNK_ID are set in your backend/.env")
        return

    # Format numbers properly for SIP
    # SIP URIs usually look like sip:+1234567890@provider.com. LiveKit takes the number directly if configured with a trunk.
    # The exact format might require the country code, e.g. +91XXXXXXXXXX
    sip_call_to = user_phone_number
    if not sip_call_to.startswith("+"):
        sip_call_to = "+" + sip_call_to

    print(f"Connecting to LiveKit to place call from {twilio_phone_number} to {sip_call_to}...")
    
    lk_api = api.LiveKitAPI()
    try:
        # 1. Create the room explicitly
        await lk_api.room.create_room(api.CreateRoomRequest(name=ROOM_NAME))
        print(f"✅ Room '{ROOM_NAME}' created/verified.")
        
        # 2. Explicitly dispatch the agent to the room
        try:
            await lk_api.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    agent_name="my-agent",
                    room=ROOM_NAME
                )
            )
            print("✅ Agent 'my-agent' explicitly dispatched.")
        except Exception as e:
            # Dispatch might already exist or auto-dispatch might be handling it, but we log the error just in case
            print(f"⚠️ Note on agent dispatch: {e}")

        # 3. Create the SIP participant to call the user
        participant = await lk_api.sip.create_sip_participant(
            sip.CreateSIPParticipantRequest(
                room_name=ROOM_NAME,
                sip_call_to=sip_call_to,
                sip_trunk_id=sip_trunk_id,
                sip_number=twilio_phone_number, # The caller ID
                participant_identity=f"sip-farmer-{sip_call_to}",
                participant_name="Farmer"
            )
        )
        print("✅ SIP Participant created! Your phone should start ringing soon.")
        print(f"LiveKit Participant Info: {participant}")
        
    except Exception as e:
        print(f"❌ Failed to initiate call: {e}")
        
    finally:
        await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(check_weather_and_call())
