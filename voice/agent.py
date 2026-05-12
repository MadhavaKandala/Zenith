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
from livekit.plugins import google as lk_google, groq as lk_groq, silero

from config.loader import load_zenith_config
from providers.manager import ZenithProviderManager
from windows_sapi_tts import WindowsSapiTTS

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

ROOT_DIR = Path(__file__).resolve().parents[1]
ROOT_ENV_PATH = ROOT_DIR / ".env"
GOOGLE_CREDENTIALS_PATH = ROOT_DIR / "core" / "config" / "voice" / "google-cloud.json"

load_dotenv(dotenv_path=ROOT_ENV_PATH)

if GOOGLE_CREDENTIALS_PATH.exists() and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GOOGLE_CREDENTIALS_PATH)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

CONFIG = load_zenith_config(ROOT_DIR / "config" / "zenith.yaml")
VOICE_CONFIG = CONFIG.get("voice", {})
LLM_CONFIG = CONFIG.get("llm", {})

STT_PROVIDER = VOICE_CONFIG.get("stt_provider", "groq_whisper")
LLM_PROVIDER = LLM_CONFIG.get("primary", "gemini")
TTS_PROVIDER = VOICE_CONFIG.get("tts_provider", "google_cloud")
GROQ_STT_MODEL = "whisper-large-v3-turbo"
GEMINI_LLM_MODEL = LLM_CONFIG.get("gemini", {}).get("model", "gemini-2.5-flash")
GOOGLE_TTS_MODEL = "gemini-2.5-flash-tts"

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
    "You are Zenith, a local-first personal AI assistant inspired by JARVIS. "
    "Be concise, accurate, and proactive. "
    "Use tools when browsing, desktop actions, or provider-chain reasoning are needed. "
    "Keep spoken answers short, usually no more than two sentences. "
    "Address the user as sir and reason in the Asia/Kolkata timezone."
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
        query: The topic to search for.
    """
    try:
        import wikipedia

        result = wikipedia.summary(query, sentences=2)
        return result
    except Exception:
        return f"I could not find information about {query}, sir."


@function_tool
async def answer_with_provider_chain(query: str) -> str:
    """Answer an open-ended question through the Gemini -> Groq -> OpenRouter chain.

    Args:
        query: The user's knowledge or reasoning request.
    """
    manager = ZenithProviderManager(CONFIG)
    messages = [
        {
            "role": "system",
            "content": (
                "You are Zenith, a local-first AI assistant. "
                "Answer precisely, stay practical, and keep the response short enough for speech."
            ),
        },
        {"role": "user", "content": query},
    ]
    try:
        return await manager.chat(messages)
    except Exception:
        return "All configured reasoning providers are unavailable right now, sir."


def _build_stt() -> lk_groq.STT:
    return lk_groq.STT(
        model=GROQ_STT_MODEL,
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

    return parsed if isinstance(parsed, dict) else {}


def _build_tts(job_metadata: dict[str, str] | None = None):
    job_metadata = job_metadata or {}
    voice_name = job_metadata.get("voiceId") or "en-US-Chirp3-HD-Achernar"
    voice_label = job_metadata.get("voiceLabel") or "Google Cloud"

    google_credentials_ready = bool(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
    )

    if google_credentials_ready:
        return (
            lk_google.TTS(
                language="en-US",
                gender="female",
                voice_name=voice_name,
                model_name=GOOGLE_TTS_MODEL,
                use_streaming=True,
            ),
            voice_label,
            voice_name,
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
    logger.info("Available session events: %s", available_session_events)

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
        logger.info("Speech created: %s", type(event).__name__)

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
                answer_with_provider_chain,
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

    await session.say(
        "Online. I am Zenith, your personal AI assistant. How can I help you today, sir?",
        allow_interruptions=True,
    )


def main() -> None:
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="zenith",
        )
    )


if __name__ == "__main__":
    main()
