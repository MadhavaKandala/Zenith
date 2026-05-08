# ZENITH - Personal AI Assistant

<p align="left">
  <a href="https://github.com/MadhavaKandala/Zenith/stargazers"><img src="https://img.shields.io/github/stars/MadhavaKandala/Zenith?style=for-the-badge" alt="Stars"></a>
  <a href="https://github.com/MadhavaKandala/Zenith/network/members"><img src="https://img.shields.io/github/forks/MadhavaKandala/Zenith?style=for-the-badge" alt="Forks"></a>
  <a href="https://github.com/MadhavaKandala/Zenith/issues"><img src="https://img.shields.io/github/issues/MadhavaKandala/Zenith?style=for-the-badge" alt="Issues"></a>
  <a href="https://github.com/MadhavaKandala/Zenith/blob/main/LICENSE.md"><img src="https://img.shields.io/github/license/MadhavaKandala/Zenith?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/Stack-Node.js%20%7C%20Python%20%7C%20Tauri%20%7C%20LiveKit-111827?style=for-the-badge" alt="Tech Stack">
</p>

**Futuristic, local-first AI command center for voice-native productivity.**

ZENITH is a personal AI assistant designed to run on your machine, route intelligence across multiple model providers, execute real tools through an MCP server, and respond through a Stark-inspired HUD and desktop shell.

---

## Showcase

ZENITH exists for builders and operators who want a private, extensible AI system that feels like a real product, not a toy bot.

- Local-first runtime keeps your workflow anchored to your own environment.
- Voice-native pipeline delivers natural interaction from microphone to response.
- Modular skills architecture lets you expand capabilities without touching the core.
- Multi-provider routing keeps the assistant responsive when one API is degraded.

### Why local-first AI matters

Most assistants are cloud UIs with fixed behavior. ZENITH is an execution layer you control:

- Your runtime and orchestration stay on your machine.
- Your skills are plain code and data, not hidden behind closed platforms.
- You choose providers, models, and fallback priority.
- You can deploy as web dashboard and desktop app from one codebase.

---

## Why Zenith?

| Capability | Zenith | Typical Assistant |
|---|---|---|
| Local-first architecture | Yes | Rare |
| Extensible skills | Yes, modular domains | Usually closed |
| Provider fallback chain | Gemini -> Groq -> OpenRouter | Usually single provider |
| Voice-native pipeline | LiveKit + STT + TTS | Often chat-only |
| Customizable stack | Models, skills, UI, desktop shell | Limited |
| Open source control | Full repository ownership | Vendor-dependent |

---

## Features

### Core Platform

| Area | What you get |
|---|---|
| Voice AI | Real-time voice interaction over LiveKit |
| HUD Dashboard | Three-panel Stark-inspired interface with state orb and tool monitor |
| AI Fallback | Automatic provider failover for resilient responses |
| Desktop Runtime | Tauri desktop packaging for native Windows app delivery |
| Skill Engine | Python-based modular skill domains with persistent behavior |
| MCP Tools | External tool execution through FastMCP server |
| Privacy Model | Local-first orchestration and self-managed configuration |

### Implemented Skills

| Domain | Skill | Purpose |
|---|---|---|
| Productivity | Reminders | Create, list, and manage personal reminders |
| Information | News | Fetch and summarize top headlines |
| Automation | Chrome / Browser | Open websites and run web searches |
| Knowledge | Q&A | General factual responses via configured LLM |
| Information | Wikipedia | Retrieve concise summaries |
| Information | Weather | Current conditions using weather APIs |
| Information | Dictionary | Definitions with spelling tolerance |
| Entertainment | YouTube | Search and open YouTube queries |
| Productivity | OCR | Extract text from image files |
| Utilities | To-do management | Task-oriented productivity interactions |
| Utilities | GitHub trending | Developer trend discovery |
| Utilities | Video downloader | Media fetch workflows |

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
                        | Gemini -> Groq -> OpenRouter|
                        +-----------------------------+
```

### Voice Pipeline (STT -> LLM -> Tool -> TTS)

```text
Mic Input
   |
   v
LiveKit Transport
   |
   v
Groq Whisper STT
   |
   v
LLM Reasoning (Gemini primary, Groq/OpenRouter fallback)
   |
   +--> Optional MCP Tool Call (news, browser, weather, OCR, etc.)
   |
   v
Google Cloud TTS
   |
   v
Speaker Output
```

### Provider Fallback Chain

```text
[Try 1] Gemini (gemini-2.5-flash)
   |
   | if error / timeout / rate limit
   v
[Try 2] Groq (llama-3.3-70b-versatile)
   |
   | if unavailable
   v
[Try 3] OpenRouter (meta-llama/llama-3.3-70b-instruct)
```

---

## Screenshots

![Zenith Dashboard](assets/dashboard.png)
![Zenith Voice Console](assets/voice-console.png)
![Zenith Tool Monitor](assets/tool-monitor.png)

---

## Technology Stack

| Layer | Technologies |
|---|---|
| LLM | Google Gemini 2.5 Flash, Groq Llama 3.3, OpenRouter |
| STT/TTS | Groq Whisper STT, Google Cloud TTS |
| Voice Transport | LiveKit |
| Tool Server | FastMCP |
| Backend | Node.js, Python |
| Frontend | JavaScript, Vite |
| Desktop | Tauri (Rust backend) |
| Skills | Modular Python skill architecture |

---

## Installation

### 1) Requirements

- Node.js `>=22`
- npm `>=10`
- Python `>=3.11`
- `uv`
- Rust + Cargo
- Visual Studio 2022 C++ Build Tools (Windows, for Tauri build)

### 2) Clone

```bash
git clone https://github.com/MadhavaKandala/Zenith.git
cd Zenith
```

### 3) Environment Setup

```bash
copy .env.sample .env
```

Set these keys in `.env`:

- `GOOGLE_API_KEY` for Gemini
- `GROQ_API_KEY` for Groq LLM and Whisper STT
- `OPENROUTER_API_KEY` for fallback routing
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` for voice transport
- `GOOGLE_APPLICATION_CREDENTIALS` path to Google Cloud service-account JSON (TTS)

### 4) Install Node Dependencies

```bash
npm install
```

### 5) Install Voice Environment

```bash
cd voice
uv sync
cd ..
```

### 6) Install Python Skill/Bridge Dependencies

```bash
cd bridges/python
pip install wikipedia requests newsapi-python pyowm pytesseract playwright tinydb --break-system-packages
python -m playwright install chromium
cd ../..
```

### 7) Verify Core Health

```bash
npm run check
```

---

## Running Zenith

ZENITH runs as three coordinated services for full voice + tool functionality.

### Method A: Three terminals

Terminal 1 (core):
```bash
npm start
```

Terminal 2 (MCP tool server):
```bash
cd voice
uv run python mcp_server.py
```

Terminal 3 (voice agent):
```bash
cd voice
uv run python agent.py dev
```

Then open:

- Dashboard: `http://localhost:1337`
- LiveKit playground: `https://agents-playground.livekit.io`

### Method B: PM2 process manager

```bash
npm install -g pm2
pm2 start npm --name zenith-core -- start
pm2 start "uv run python mcp_server.py" --name zenith-mcp --cwd voice
pm2 start "uv run python agent.py dev" --name zenith-voice --cwd voice
pm2 save
pm2 logs
```

### Method C: Desktop app

```bash
npm run tauri:dev
```

Production desktop build:

```bash
npm run tauri:build
```

---

## Skills Reference

### Custom Skills (Current)

- `reminders`: persistent reminders and follow-ups
- `news`: global headlines
- `chrome`: browser opening and search automation
- `qa`: open-domain question handling
- `wiki`: Wikipedia summaries
- `weather`: weather conditions lookup
- `dictionary`: meaning + correction support
- `youtube`: query-based video search
- `ocr`: text extraction from images

### Built-in Skill Support

ZENITH also includes built-in assistant capabilities provided by the core runtime, with routing through `core/langs.json` fallback entries.

### Add a New Skill

Create a new module with:

- `skill.py` logic file
- `data/expressions/en.json` trigger phrases
- `data/answers/en.json` responses
- `skill.json` metadata
- `config/en.json` and `config/config.sample.json`

Then register fallback words in `core/langs.json` and restart core.

---

## Folder Structure

```text
Zenith/
|- app/                    # HUD frontend (Vite + vanilla JS)
|- config/                 # provider and runtime config
|  |- zenith.yaml
|  |- zenith.example.yaml
|- core/                   # assistant core and language routing
|- providers/              # Gemini/Groq/OpenRouter abstraction
|- skills/                 # custom and built-in skills
|  |- productivity/
|  |- information/
|  |- automation/
|  |- knowledge/
|  |- entertainment/
|- voice/                  # voice agent + MCP server
|  |- agent.py
|  |- mcp_server.py
|- bridges/python/         # python bridge dependencies
|- src-tauri/              # desktop packaging and Rust runtime
`- README.md
```

---

## Roadmap

- Multilingual voice and skill support
- Face authentication and identity profiles
- Custom wake-word engine
- Long-term memory with contextual recall
- Mobile companion application
- Autonomous skill generation pipeline

---

## Future Vision

ZENITH is positioned as a personal AI operating layer rather than a single chatbot. The next evolution is a persistent local intelligence fabric: voice-native interaction, autonomous task execution, dynamic skill synthesis, and cross-device presence with strict owner control over data, providers, and behavior.

---

## Contributing

Contributions are welcome for:

- new skills and tool integrations
- performance and reliability improvements
- voice UX quality upgrades
- dashboard and desktop polish

Workflow:

1. Fork the repo
2. Create a feature branch
3. Commit focused changes
4. Open a pull request with test notes

---

## License

This project is licensed under the MIT License. See `LICENSE.md`.

---

## Creator

Created and maintained by **Madhava Kandala**.

GitHub: [https://github.com/MadhavaKandala](https://github.com/MadhavaKandala)
