import asyncio
import datetime
import json
import logging
import os
import sys
import webbrowser
from pathlib import Path
from typing import get_args

import pytz
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import ChatMessage, function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.events import EventTypes
from livekit.plugins import (
    elevenlabs as lk_elevenlabs,
    google as lk_google,
    groq as lk_groq,
    silero,
)

from windows_sapi_tts import WindowsSapiTTS

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

ROOT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ROOT_ENV_PATH)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

print("API Keys loaded:")
print("  GOOGLE:", "OK" if os.getenv("GOOGLE_API_KEY") else "MISSING")
print("  GROQ:", "OK" if os.getenv("GROQ_API_KEY") else "MISSING")
print(
    "  ELEVENLABS:",
    "OK"
    if os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
    else "MISSING",
)
print("  LIVEKIT URL:", os.getenv("LIVEKIT_URL", "MISSING"))

STT_PROVIDER = "groq_whisper"
LLM_PROVIDER = "gemini"
TTS_PROVIDER = "elevenlabs"
GROQ_STT_MODEL = "whisper-large-v3-turbo"
GEMINI_LLM_MODEL = "gemini-2.5-flash"
ELEVENLABS_TTS_MODEL = "eleven_turbo_v2_5"
SITE_LABELS = {
    "youtube": "YouTube",
    "github": "GitHub",
    "gmail": "Gmail",
    "google": "Google",
    "maps": "Google Maps",
    "stackoverflow": "Stack Overflow",
    "netflix": "Netflix",
    "spotify": "Spotify",
    "twitter": "Twitter",
    "instagram": "Instagram",
    "whatsapp": "WhatsApp",
    "linkedin": "LinkedIn",
}

SITES = {
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "maps": "https://maps.google.com",
    "stackoverflow": "https://stackoverflow.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "twitter": "https://www.twitter.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "linkedin": "https://www.linkedin.com",
}


SYSTEM_PROMPT = (
    "You are Zenith, a personal AI assistant like "
    "JARVIS from Iron Man. Be extremely concise - "
    "maximum 2 sentences for voice output. "
    "Address the user as sir. "
    "You are in India, timezone IST."
)

logger = logging.getLogger("zenith-agent")
logger.setLevel(logging.INFO)


@function_tool
async def open_application(url_or_app: str) -> str:
    """Open a website or application on the user's computer.

    Args:
        url_or_app: The URL or application name to open.
    """
    target = url_or_app.lower().strip()

    for name, url in SITES.items():
        if name in target:
            webbrowser.open(url)
            return f"Opening {SITE_LABELS[name]} for you, sir."

    if target.startswith("http"):
        webbrowser.open(target)
        return f"Opening {target} for you, sir."

    search_url = f"https://www.google.com/search?q={url_or_app}"
    webbrowser.open(search_url)
    return f"Searching for {url_or_app} on Google, sir."


@function_tool
async def get_current_time() -> str:
    """Get the current date and time."""
    now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    return now.strftime("It is %I:%M %p IST on %A, %B %d, %Y, sir.")


@function_tool
async def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information about a topic.

    Args:
        query: The topic to search for
    """
    try:
        import wikipedia

        result = wikipedia.summary(query, sentences=2)
        return result
    except Exception:
        return f"I could not find information about {query}, sir."


def _build_stt() -> lk_groq.STT:
    return lk_groq.STT(
        model="whisper-large-v3-turbo",
        api_key=os.getenv("GROQ_API_KEY"),
        language="en",
    )


def _build_llm():
    return lk_google.LLM(
        model=GEMINI_LLM_MODEL,
        api_key=os.getenv("GOOGLE_API_KEY"),
    )


def _build_vad():
    return silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=1.5,
        prefix_padding_duration=0.2,
        activation_threshold=0.6,
    )


def _parse_job_metadata(ctx: JobContext) -> dict[str, str]:
    raw_metadata = getattr(ctx.job, "metadata", "") or ""
    if not raw_metadata:
        return {}

    try:
        parsed = json.loads(raw_metadata)
    except json.JSONDecodeError:
        logger.warning("Unable to parse job metadata: %s", raw_metadata)
        return {}

    if isinstance(parsed, dict):
        return parsed

    return {}


def _build_tts(job_metadata: dict[str, str] | None = None):
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
    job_metadata = job_metadata or {}
    elevenlabs_voice_id = job_metadata.get("voiceId") or os.getenv(
        "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"
    )
    elevenlabs_voice_label = job_metadata.get("voiceLabel") or "Rachel"

    if elevenlabs_key:
        return (
            lk_elevenlabs.TTS(
                api_key=elevenlabs_key,
                voice_id=elevenlabs_voice_id,
                model=ELEVENLABS_TTS_MODEL,
            ),
            elevenlabs_voice_label,
            elevenlabs_voice_id,
        )

    return WindowsSapiTTS(), "Windows SAPI", "local-fallback"


def _extract_message_text(message: ChatMessage) -> str:
    parts = []

    for item in message.content:
        if isinstance(item, str):
            parts.append(item)
            continue

        text = getattr(item, "text", None)
        if isinstance(text, str) and text.strip():
            parts.append(text)

    return " ".join(part.strip() for part in parts if part and part.strip())


def _register_session_debug_handlers(session: AgentSession) -> None:
    available_session_events = list(get_args(EventTypes))
    print("Available session events:", available_session_events)

    @session.on("user_input_transcribed")
    def on_user_input(event) -> None:
        if event.is_final and event.transcript.strip():
            print(f"\n>>> USER: {event.transcript.strip()}")

    @session.on("conversation_item_added")
    def on_agent_response(event) -> None:
        if getattr(event.item, "role", None) != "assistant":
            return

        text = _extract_message_text(event.item)
        if text:
            print(f"<<< ZENITH: {text}\n")

    @session.on("speech_created")
    def on_speech_created(event) -> None:
        logger.info("Speech created")

    @session.on("agent_state_changed")
    def on_state_change(event) -> None:
        logger.info("Agent: %s -> %s", event.old_state, event.new_state)

    @session.on("error")
    def on_error(event) -> None:
        logger.error("Error: %s", event.error)


class ZenithAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            tools=[
                open_application,
                get_current_time,
                search_wikipedia,
            ],
        )


async def _wait_for_remote_participant(ctx: JobContext, timeout: float = 15.0):
    if ctx.room.remote_participants:
        return next(iter(ctx.room.remote_participants.values()))

    loop = asyncio.get_running_loop()
    participant_future = loop.create_future()

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant) -> None:
        if not participant_future.done():
            participant_future.set_result(participant)

    try:
        return await asyncio.wait_for(participant_future, timeout=timeout)
    except asyncio.TimeoutError:
        return None


async def entrypoint(ctx: JobContext) -> None:
    job_metadata = _parse_job_metadata(ctx)
    tts, selected_voice_label, selected_voice_id = _build_tts(job_metadata)

    logger.info(
        "Zenith online - room: %s | STT=%s | LLM=%s | TTS=%s",
        ctx.room.name,
        STT_PROVIDER,
        LLM_PROVIDER,
        TTS_PROVIDER,
    )
    logger.info(
        "Voice preset selected: %s (%s)",
        selected_voice_label,
        selected_voice_id,
    )

    await ctx.connect()
    logger.info("Connected to room successfully")

    session = AgentSession(
        stt=_build_stt(),
        llm=_build_llm(),
        tts=tts,
        vad=_build_vad(),
        turn_detection="vad",
        min_endpointing_delay=0.05,
        max_endpointing_delay=0.35,
    )

    _register_session_debug_handlers(session)

    await session.start(agent=ZenithAgent(), room=ctx.room)
    participant = await _wait_for_remote_participant(ctx)
    if participant is not None:
        logger.info("Remote participant connected: %s", participant.identity)
    else:
        logger.warning("No remote participant joined before greeting timeout")

    logger.info("Starting greeting speech")
    await session.say(
        "Online. I am Zenith, your personal AI assistant. "
        "How can I help you today, sir?",
        allow_interruptions=True,
    )
    logger.info("Greeting speech finished")


def main() -> None:
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="zenith",
        )
    )


if __name__ == "__main__":
    main()
