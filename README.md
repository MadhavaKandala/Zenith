# ZENITH — Personal AI Assistant

<p align="left">
  <img src="https://img.shields.io/badge/Stack-Node.js%20%7C%20Python%20%7C%20Tauri%20%7C%20LiveKit-111827?style=for-the-badge" alt="Tech Stack">
  <img src="https://img.shields.io/badge/version-1.0.0--beta.8-6366f1?style=for-the-badge" alt="Version">
</p>

**Futuristic, local-first AI command center for voice-native productivity.**

ZENITH is a personal AI assistant that runs entirely on your machine. It routes intelligence across multiple LLM providers, executes real tools through an MCP server, and presents everything through a Stark-inspired HUD and native desktop shell.

---

## What Makes ZENITH Different

Most AI assistants are cloud UIs with fixed behavior. ZENITH is an execution layer you own:

- **Local-first** — your runtime and orchestration stay on your machine
- **Voice-native** — microphone input to spoken response in one seamless pipeline
- **Multi-provider resilience** — automatic failover across Gemini, Groq, and OpenRouter
- **Extensible skills** — add new capabilities as plain Python modules without touching the core
- **One codebase** — ships as both a web dashboard and a native desktop app via Tauri

---

## Core Features

| Area | Description |
|---|---|
| Voice AI | Real-time voice interaction over LiveKit (STT → LLM → TTS) |
| HUD Dashboard | Three-panel Stark-inspired interface with state orb and tool monitor |
| AI Fallback | Automatic provider failover: Gemini → Groq → OpenRouter |
| Desktop Runtime | Tauri packaging for a native Windows desktop app |
| Skill Engine | Modular Python skill domains with persistent behavior |
| MCP Tools | External tool execution via FastMCP server |
| Privacy Model | Local-first orchestration, self-managed keys and config |

---

## Implemented Skills

| Skill | What it does |
|---|---|
| Reminders | Create, list, and manage personal reminders |
| To-do list | Task-oriented productivity management |
| News | Fetch and summarize top headlines |
| Browser | Open websites and run web searches |
| Q&A | General factual responses via the configured LLM |
| Wikipedia | Retrieve concise article summaries |
| Weather | Current conditions via weather API |
| Dictionary | Word definitions with spelling tolerance |
| YouTube | Search and open YouTube queries |
| OCR | Extract text from image files |

---

## System Architecture

```text
                      +-----------------------+
                      |   Zenith HUD / Tauri  |
                      |  (Web + Desktop UI)   |
                      +-----------+-----------+
                                  |
                                  v
                    +-----------------------------+
                    |   Core Orchestrator Layer   |
                    |  (Node.js + skill routing)  |
                    +-----+-------------------+---+
                          |                   |
                          |                   v
                          |        +----------------------+
                          |        |  Python MCP Server   |
                          |        |  (FastMCP tools)     |
                          |        +----------+-----------+
                          |                   |
                          v                   v
                  +---------------+   +--------------------+
                  | Skill Engine  |   | External Actions   |
                  | (Python mods) |   | Browser, OCR, APIs |
                  +-------+-------+   +--------------------+
                          |
                          v
                    +-----------------------------+
                    |   LLM Provider Manager      |
                    | Gemini → Groq → OpenRouter  |
                    +-----------------------------+
```

### Voice Pipeline

```text
Mic Input → LiveKit Transport → Groq Whisper STT
  → LLM Reasoning (Gemini primary, Groq/OpenRouter fallback)
    → [Optional MCP Tool Call]
      → ElevenLabs TTS (Windows SAPI fallback) → Speaker Output
```

### Provider Fallback Chain

```text
[1] Gemini (gemini-2.5-flash)
  ↓ on error / timeout / rate limit
[2] Groq (llama-3.3-70b-versatile)
  ↓ on unavailability
[3] OpenRouter (meta-llama/llama-3.3-70b-instruct)
```

---

## Technology Stack

| Layer | Technologies |
|---|---|
| LLM | Google Gemini 2.5 Flash, Groq Llama 3.3, OpenRouter |
| STT / TTS | Groq Whisper STT, ElevenLabs TTS, Windows SAPI fallback |
| Voice Transport | LiveKit |
| Tool Server | FastMCP |
| Backend | Node.js, Python |
| Frontend | JavaScript, Vite |
| Desktop | Tauri (Rust backend) |

---

## Installation

### Requirements

- Node.js `>=22`, npm `>=10`
- Python `>=3.11`
- `uv` (Python package manager)
- Rust + Cargo
- Visual Studio 2022 C++ Build Tools (Windows, required for Tauri)

### Clone

```bash
git clone https://github.com/Madhavakandala/zenith.git
cd zenith
```

### Environment Setup

```bash
copy .env.sample .env
```

Fill in your keys in `.env`:

| Key | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Gemini LLM |
| `GROQ_API_KEY` | Groq LLM + Whisper STT |
| `OPENROUTER_API_KEY` | Fallback routing |
| `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` | Voice transport |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON (TTS) |

### Install Dependencies

```bash
# Node dependencies
npm install

# Voice environment
cd voice && uv sync && cd ..

# Python skill/bridge dependencies
cd bridges/python
pip install wikipedia requests newsapi-python pyowm pytesseract playwright tinydb --break-system-packages
python -m playwright install chromium
cd ../..
```

### Verify Setup

```bash
npm run check
```

---

## Running ZENITH

ZENITH runs as three coordinated services.

### Three Terminals

```bash
# Terminal 1 — core server
npm start

# Terminal 2 — MCP tool server
cd voice && uv run python mcp_server.py

# Terminal 3 — voice agent
cd voice && uv run python agent.py dev
```

Then open:
- Dashboard: `http://localhost:1337`
- Voice playground: `https://agents-playground.livekit.io`

### Voice Controls

- `ACTIVATE VOICE` starts a LiveKit voice room.
- `END VOICE` fully disconnects the room, even if Zenith is still connecting or thinking.
- `ANSWER NOW` pauses the microphone and forces Zenith to answer from captured speech.
- `RESUME MIC` reopens the microphone without reconnecting the whole session.

### PM2 (Recommended for persistent sessions)

```bash
npm install -g pm2
pm2 start npm --name zenith-core -- start
pm2 start "uv run python mcp_server.py" --name zenith-mcp --cwd voice
pm2 start "uv run python agent.py dev" --name zenith-voice --cwd voice
pm2 save && pm2 logs
```

### Desktop App

```bash
# Development
npm run tauri:dev

# Production build
npm run tauri:build
```

---

## Folder Structure

```text
zenith/
├── app/              # HUD frontend (Vite + vanilla JS)
├── config/           # Provider and runtime config
├── core/             # Assistant core and language routing
├── providers/        # Gemini / Groq / OpenRouter abstraction
├── skills/           # Skill domains (Python modules)
│   ├── productivity/
│   ├── information/
│   ├── automation/
│   ├── knowledge/
│   └── entertainment/
├── voice/            # Voice agent (agent.py) + MCP server
├── bridges/python/   # Python bridge dependencies
└── src-tauri/        # Desktop packaging and Rust runtime
```

---

## Adding a New Skill

Each skill is a self-contained Python module. Create a directory under `skills/<domain>/<skill-name>/` containing:

- `skill.py` — core logic
- `data/expressions/en.json` — trigger phrases
- `data/answers/en.json` — canned responses
- `skill.json` — metadata
- `config/en.json` + `config/config.sample.json` — configuration

Register fallback words in `core/langs.json` and restart core.

---

## Contributing

Contributions are welcome for new skills, tool integrations, voice UX improvements, and dashboard polish.

1. Fork the repository
2. Create a feature branch
3. Commit focused, well-described changes
4. Open a pull request with test notes

---

## Creator

Built and maintained by **Madhava Kandala** — [github.com/Madhavakandala](https://github.com/Madhavakandala)
