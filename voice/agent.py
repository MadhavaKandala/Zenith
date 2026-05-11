import logging
import os
import json
import subprocess
import webbrowser
from pathlib import Path
from typing import get_args

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import ChatMessage, mcp, function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.events import EventTypes
from livekit.plugins import google as lk_google, groq as lk_groq, silero

ROOT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ROOT_ENV_PATH)

STT_PROVIDER = "groq_whisper"
LLM_PROVIDER = "gemini"
TTS_PROVIDER = "google_cloud"
GROQ_STT_MODEL = "whisper-large-v3-turbo"
GEMINI_LLM_MODEL = "gemini-2.5-flash"
GOOGLE_TTS_VOICE = "en-US-Neural2-D"
MCP_SERVER_PORT = 8000

SYSTEM_PROMPT = """You are Zenith, a personal AI assistant in the 
style of JARVIS from Iron Man. Be concise, helpful, and address 
the user as sir. You have the ability to open websites and 
applications. When the user asks to open something, use the 
open_application tool. Keep responses under 3 sentences for 
voice output."""

logger = logging.getLogger("zenith-agent")
logger.setLevel(logging.INFO)


@function_tool
async def open_application(url_or_app: str) -> str:
    """Open a website or application on the user's computer.
    
    Args:
        url_or_app: The URL or application name to open.
                   Examples: 'youtube', 'github', 'gmail', 
                   'https://youtube.com'
    """
    sites = {
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

    target = url_or_app.lower().strip()
    
    # Check known sites
    for name, url in sites.items():
        if name in target:
            webbrowser.open(url)
            return f"Opening {name.capitalize()} for you, sir."
    
    # If it looks like a URL already
    if target.startswith("http"):
        webbrowser.open(target)
        return f"Opening {target} for you, sir."
    
    # Search Google for anything else
    search_url = f"https://www.google.com/search?q={url_or_app}"
    webbrowser.open(search_url)
    return f"Searching for {url_or_app} on Google, sir."


@function_tool  
async def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    now = datetime.now()
    return now.strftime("It is %I:%M %p on %A, %B %d, %Y, sir.")


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
    except Exception as e:
        return f"I could not find information about {query}, sir."


def _mcp_server_url() -> str:
    return f"http://127.0.0.1:{MCP_SERVER_PORT}/sse"


def _build_stt():
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


def _build_tts():
    return lk_google.TTS(
        language="en-US",
        voice_name=GOOGLE_TTS_VOICE,
        speaking_rate=1.0,
        use_streaming=True,
    )


def _extract_message_text(message: ChatMessage) -> str:
    parts = []
    for item in message.content:
        if isinstance(item, str):
            parts.append(item)
        else:
            text = getattr(item, "text", None)
            if isinstance(text, str) and text.strip():
                parts.append(text)
    return " ".join(p.strip() for p in parts if p and p.strip())


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


async def entrypoint(ctx: JobContext) -> None:
    logger.info("Zenith online - room: %s", ctx.room.name)

    session = AgentSession(
        stt=_build_stt(),
        llm=_build_llm(),
        tts=_build_tts(),
        vad=silero.VAD.load(),
        turn_detection="vad",
        min_endpointing_delay=0.3,
    )

    @session.on("user_input_transcribed")
    def on_user_input(event):
        if event.is_final and event.transcript.strip():
            print(f"\n>>> USER: {event.transcript.strip()}")

    @session.on("conversation_item_added")
    def on_agent_response(event):
        if getattr(event.item, "role", None) == "assistant":
            text = _extract_message_text(event.item)
            if text:
                print(f"<<< ZENITH: {text}\n")

    @session.on("agent_state_changed")
    def on_state_change(event):
        logger.info("Agent: %s → %s", event.old_state, event.new_state)

    @session.on("error")
    def on_error(event):
        logger.error("Error: %s", event.error)

    await session.start(agent=ZenithAgent(), room=ctx.room)
    await session.say(
        "Online. I am Zenith, your personal AI assistant. "
        "How can I help you today, sir?",
        allow_interruptions=True,
    )


def main() -> None:
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="zenith",
    ))


if __name__ == "__main__":
    main()
