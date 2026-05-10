import logging
import os
from pathlib import Path
from typing import get_args

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import ChatMessage, mcp
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.events import EventTypes
from livekit.plugins import google as lk_google, groq as lk_groq, silero

STT_PROVIDER = "groq_whisper"
LLM_PROVIDER = "gemini"
TTS_PROVIDER = "google_cloud"

GROQ_STT_MODEL = "whisper-large-v3-turbo"
GEMINI_LLM_MODEL = "gemini-2.5-flash"
GOOGLE_TTS_VOICE = "en-US-Neural2-D"
MCP_SERVER_PORT = 8000

SYSTEM_PROMPT = (
    "You are Zenith, a personal AI assistant in the style of JARVIS from Iron Man. "
    "Be concise, helpful, and address the user as sir."
)

ROOT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ROOT_ENV_PATH)

logger = logging.getLogger("zenith-agent")
logger.setLevel(logging.INFO)


def _mcp_server_url() -> str:
    url = f"http://127.0.0.1:{MCP_SERVER_PORT}/sse"
    logger.info("MCP Server URL: %s", url)
    return url


def _build_stt() -> lk_groq.STT:
    logger.info("STT -> Groq Whisper (%s)", GROQ_STT_MODEL)
    return lk_groq.STT(
        model=GROQ_STT_MODEL,
        api_key=os.getenv("GROQ_API_KEY"),
        language="en",
    )


def _build_llm() -> lk_google.LLM:
    logger.info("LLM -> Google Gemini (%s)", GEMINI_LLM_MODEL)
    return lk_google.LLM(
        model=GEMINI_LLM_MODEL,
        api_key=os.getenv("GOOGLE_API_KEY"),
    )


def _build_tts() -> lk_google.TTS:
    logger.info("TTS -> Google Cloud TTS (%s)", GOOGLE_TTS_VOICE)
    return lk_google.TTS(
        language="en-US",
        voice_name=GOOGLE_TTS_VOICE,
        speaking_rate=1.0,
        use_streaming=True,
    )


def _extract_message_text(message: ChatMessage) -> str:
    parts: list[str] = []

    for item in message.content:
        if isinstance(item, str):
            parts.append(item)
            continue

        text = getattr(item, "text", None)
        if isinstance(text, str) and text.strip():
            parts.append(text)
            continue

        if isinstance(item, dict):
            dict_text = item.get("text")
            if isinstance(dict_text, str) and dict_text.strip():
                parts.append(dict_text)

    return " ".join(part.strip() for part in parts if part and part.strip())


class ZenithAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            mcp_servers=[
                mcp.MCPServerHTTP(
                    url=_mcp_server_url(),
                    transport_type="sse",
                    client_session_timeout_seconds=30,
                ),
            ],
        )


def _turn_detection() -> str:
    return "vad"


def _endpointing_delay() -> float:
    return 0.3


def _register_session_debug_handlers(session: AgentSession) -> None:
    available_session_events = list(get_args(EventTypes))
    print("Available session events:", available_session_events)

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event) -> None:
        if event.is_final and event.transcript.strip():
            print(f"USER SAID: {event.transcript.strip()}")

    @session.on("conversation_item_added")
    def on_conversation_item_added(event) -> None:
        item = event.item
        if getattr(item, "role", None) != "assistant":
            return

        agent_text = _extract_message_text(item)
        if agent_text:
            print(f"ZENITH SAID: {agent_text}")

    @session.on("user_state_changed")
    def on_user_state_changed(event) -> None:
        logger.info("User state: %s -> %s", event.old_state, event.new_state)

    @session.on("agent_state_changed")
    def on_agent_state_changed(event) -> None:
        logger.info("Agent state: %s -> %s", event.old_state, event.new_state)

    @session.on("error")
    def on_session_error(event) -> None:
        logger.error("Session error from %s: %s", type(event.source).__name__, event.error)


async def entrypoint(ctx: JobContext) -> None:
    logger.info(
        "Zenith online - room: %s | STT=%s | LLM=%s | TTS=%s",
        ctx.room.name,
        STT_PROVIDER,
        LLM_PROVIDER,
        TTS_PROVIDER,
    )

    session = AgentSession(
        stt=_build_stt(),
        llm=_build_llm(),
        tts=_build_tts(),
        vad=silero.VAD.load(),
        turn_detection=_turn_detection(),
        min_endpointing_delay=_endpointing_delay(),
    )
    _register_session_debug_handlers(session)

    await session.start(agent=ZenithAgent(), room=ctx.room)
    await session.say(
        "Hello sir. I am Zenith, your personal AI assistant. How can I help you?",
        allow_interruptions=True,
    )


def main() -> None:
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="zenith",
        )
    )


def dev() -> None:
    import sys

    if len(sys.argv) == 1:
        sys.argv.append("dev")

    main()


if __name__ == "__main__":
    main()
