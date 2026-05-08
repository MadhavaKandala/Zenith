<div align="center">

# ⚡ ZENITH

### Your Personal AI Assistant

*Voice-powered. Locally hosted. Fully yours.*

![Node](https://img.shields.io/badge/Node.js-22%2B-339933?style=flat-square&logo=node.js&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-4285F4?style=flat-square&logo=google&logoColor=white)
![Tauri](https://img.shields.io/badge/Desktop-Tauri-FFC131?style=flat-square&logo=tauri&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-00D4FF?style=flat-square)

</div>

---

Zenith is a personal AI assistant that runs on your own machine. Speak to it naturally — it listens, thinks, executes real tools, and responds back in a synthesized voice through a futuristic Tony Stark-inspired HUD dashboard.

No subscriptions. No data leaving your machine without your control. Your API keys, your models, your assistant.

---

## Features

- **Voice interaction** — speak naturally, Zenith listens and responds with a voice
- **9 skill domains** — reminders, news, Q&A, web browsing, Wikipedia, weather, dictionary, YouTube, OCR
- **Smart AI fallback** — Gemini as the primary brain, automatically switches to Groq or OpenRouter if needed
- **Futuristic HUD** — three-panel dark dashboard with animated voice orb and live tool monitor
- **Native desktop app** — runs as a proper Windows application via Tauri
- **Fully extensible** — add new skills by dropping in a folder, no core changes needed
- **Local-first** — runs on your hardware, your API keys, your data

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Brain (primary) | Google Gemini 2.5 Flash |
| AI Brain (fallback) | Groq llama-3.3-70b → OpenRouter |
| Voice Input (STT) | Groq Whisper large-v3-turbo |
| Voice Output (TTS) | Google Cloud TTS — Neural2-D |
| Voice Transport | LiveKit Agents |
| Skills Engine | NLU classifier + Python skill bridge |
| Web UI | Vanilla JS + Vite — dark HUD theme |
| Desktop App | Tauri (native Windows) |
| Tool Server | FastMCP over SSE |

---

## Prerequisites

### Software

| Software | Version | Check |
|----------|---------|-------|
| Node.js | ≥ 22.x | `node --version` |
| npm | ≥ 10.x | `npm --version` |
| Python | ≥ 3.11 | `python --version` |
| uv | any | `uv --version` |
| Git | any | `git --version` |
| Rust + Cargo | any | `rustc --version` |

> **Windows only:** Tauri requires Visual Studio C++ Build Tools.
> Install with: `winget install Microsoft.VisualStudio.2022.BuildTools`

### API Keys

You need free accounts for these services. None require a credit card.

| Key | Powers | Get it | Free tier |
|-----|--------|--------|-----------|
| `GOOGLE_API_KEY` | Gemini AI (primary brain) | [aistudio.google.com](https://aistudio.google.com) | 1M tokens/day |
| `GROQ_API_KEY` | Whisper STT + Llama fallback | [console.groq.com](https://console.groq.com) | 14,400 req/day |
| `LIVEKIT_URL` | Voice transport | [cloud.livekit.io](https://cloud.livekit.io) | 3 concurrent rooms |
| `LIVEKIT_API_KEY` | LiveKit auth | [cloud.livekit.io](https://cloud.livekit.io) | Free |
| `LIVEKIT_API_SECRET` | LiveKit auth | [cloud.livekit.io](https://cloud.livekit.io) | Free |
| `GOOGLE_APPLICATION_CREDENTIALS` | Voice output (TTS) | [console.cloud.google.com](https://console.cloud.google.com) | 1M chars/month |
| `OPENROUTER_API_KEY` | Tertiary AI fallback *(optional)* | [openrouter.ai](https://openrouter.ai) | $1 free credit |
| `NEWS_API_KEY` | News headlines skill | [newsapi.org](https://newsapi.org) | 100 req/day |
| `OPENWEATHER_API_KEY` | Weather skill | [openweathermap.org](https://openweathermap.org) | 1,000 req/day |

> **Google Cloud TTS setup:** Go to [console.cloud.google.com](https://console.cloud.google.com) → enable the Text-to-Speech API → create a Service Account → download the JSON key file → set `GOOGLE_APPLICATION_CREDENTIALS` to its full path.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/MadhavaKandala/Zenith.git
cd Zenith
```

### 2. Set up environment variables

```bash
copy .env.sample .env
```

Open `.env` and fill in all your API keys:

```env
# AI Providers
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-...        # optional

# Voice (LiveKit)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxx

# Voice Output (Google Cloud TTS)
GOOGLE_APPLICATION_CREDENTIALS=C:\full\path\to\gcp-key.json

# Skill APIs
NEWS_API_KEY=xxxxxxxxxxxxxxxx
OPENWEATHER_API_KEY=xxxxxxxxxxxxxxxx
```

> ⚠️ Never commit your `.env` file. It is already in `.gitignore`.

### 3. Install Node.js dependencies

```bash
npm install
```

### 4. Install Python voice dependencies

```bash
cd voice
uv sync
cd ..
```

### 5. Install Python skill dependencies

```bash
cd bridges\python
pip install wikipedia requests newsapi-python pyowm pytesseract playwright tinydb --break-system-packages
python -m playwright install chromium
cd ..\..
```

### 6. Verify the installation

```bash
# Check Leon/Zenith core
leon check

# Check AI providers
python -c "from providers.manager import ZenithProviderManager; print('All providers OK')"
```

---

## Running Zenith

Zenith needs three processes running simultaneously.

### Option A — Three terminals

**Terminal 1 — Core engine**
```bash
npm start
# Wait for: "Server is listening on port 1337"
# Then open: http://localhost:1337
```

**Terminal 2 — Tool server**
```bash
cd voice
uv run python mcp_server.py
# Wait for: "Uvicorn running on http://0.0.0.0:8000"
```

**Terminal 3 — Voice agent**
```bash
cd voice
uv run python agent.py
# Wait for: "Agent connected"
```

### Option B — pm2 (recommended for daily use)

```bash
# One-time setup
npm install -g pm2
pm2 start "npm start" --name "zenith-core"
pm2 start "uv run python voice/mcp_server.py" --name "zenith-mcp"
pm2 start "uv run python voice/agent.py" --name "zenith-voice"
pm2 save
pm2 startup

# Every day
pm2 start all      # start
pm2 stop all       # stop
pm2 status         # check
pm2 restart all    # after code changes
```

### Option C — Desktop app

```bash
# Run the built executable
src-tauri\target\release\zenith.exe

# Or in development mode
npx tauri dev
```

> The desktop app is a native window wrapper. The three backend processes must still be running.

---

## Using Zenith

### Text mode

Open [http://localhost:1337](http://localhost:1337) — type in the input box and press Enter.

### Voice mode

1. Go to [https://agents-playground.livekit.io](https://agents-playground.livekit.io)
2. Connect using your LiveKit URL, API key, and secret
3. Click the microphone and speak

---

## Skills

### Reminders
```
"Remind me to call the doctor"
"Set a reminder for the team standup"
"What are my reminders?"
"Delete my reminders"
```

### News
```
"What are today's headlines?"
"Read me the news"
"What's happening in the world?"
```

### Web & Browser
```
"Open YouTube"
"Open GitHub"
"Search for Python tutorials"
"Browse to Google Maps"
```

### Q&A (powered by Gemini)
```
"What is quantum computing?"
"Explain the difference between TCP and UDP"
"How does photosynthesis work?"
```
*Any factual question — routed directly to Gemini.*

### Wikipedia
```
"Search Wikipedia for Nikola Tesla"
"Tell me about the Roman Empire"
"Wikipedia: artificial intelligence"
```

### Weather
```
"What's the weather today?"
"Weather in Hyderabad"
"Is it going to rain?"
```

### Dictionary
```
"Define serendipity"
"What does ephemeral mean?"
"Dictionary: resilience"
```

### YouTube
```
"Play lo-fi music on YouTube"
"YouTube: coding tutorials"
"Search YouTube for Python beginner guide"
```

### OCR — Read text from images
```
"Read the text in this image"
"Extract text from screenshot"
```
*Requires Tesseract installed at system level.*

### Built-in skills
| Skill | Example |
|-------|---------|
| To-do list | "Add buy milk to my to-do list" |
| Is it down? | "Is GitHub down?" |
| GitHub trending | "What's trending on GitHub?" |
| Video downloader | "Download: [YouTube URL]" |

---

## The Dashboard

Open [http://localhost:1337](http://localhost:1337) to see the three-panel HUD:

| Panel | What it shows |
|-------|--------------|
| **Left — Orb** | Voice state animation: IDLE / LISTENING / THINKING / SPEAKING |
| **Centre — Chat** | Full conversation history and text input |
| **Right — Tool Monitor** | Live feed of every tool Zenith activates, with timestamps |

---

## AI Provider System

Zenith uses an automatic three-tier fallback chain:

```
Gemini 2.5 Flash  →  Groq llama-3.3  →  OpenRouter
   (primary)            (fallback)         (backup)
```

If one provider is unavailable or rate-limited, the next activates instantly — no action needed from you.

To change models, edit `config/zenith.yaml`:

```yaml
llm:
  gemini:
    model: "gemini-2.5-flash"         # or gemini-2.5-pro
  groq:
    model: "llama-3.3-70b-versatile"
```

---

## Adding a New Skill

Every skill is a self-contained folder:

```
skills/{domain}/{skill_name}/
├── __init__.py
├── {skill_name}.py           ← your logic
├── skill.json                ← metadata
├── data/
│   ├── expressions/en.json   ← trigger phrases
│   └── answers/en.json       ← response templates
└── config/
    └── config.sample.json
```

See `ZENITH_DOCUMENTATION.docx` for a full step-by-step walkthrough with a working example.

---

## Project Structure

```
Zenith/
├── skills/                   All skill plugins (9 domains)
├── voice/                    Voice pipeline
│   ├── agent.py              LiveKit voice agent
│   ├── mcp_server.py         FastMCP tool server
│   └── friday_tools/         Web search + system tools
├── providers/                AI provider abstraction
│   ├── manager.py            Fallback chain
│   ├── gemini.py
│   ├── groq_provider.py
│   └── openrouter_provider.py
├── config/
│   ├── zenith.yaml           Main configuration
│   └── zenith.example.yaml   Template
├── app/src/                  Web dashboard (Vite)
│   ├── index.html            HUD layout
│   ├── css/style.css         Dark theme + animations
│   └── js/
│       ├── orb.js            Voice orb animation
│       ├── monitor.js        Tool monitor
│       └── client.js         WebSocket events
├── server/                   NLU engine + HTTP/WS API
├── hotword/                  Wake word detector
├── bridges/python/           Python skill bridge
├── src-tauri/                Desktop app (Tauri)
│   └── target/release/
│       └── zenith.exe        Built Windows executable
├── .env                      Your API keys (never commit)
└── ZENITH_DOCUMENTATION.docx Full setup & user guide
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 1337 in use | `netstat -ano \| findstr :1337` — kill that process |
| npm install fails | Delete `node_modules/` and run `npm install` again |
| Voice agent crashes | `cd voice && uv sync` to reinstall dependencies |
| No voice output | Check `GOOGLE_APPLICATION_CREDENTIALS` path in `.env` |
| Gemini not responding | Check rate limits at aistudio.google.com — Groq auto-activates as fallback |
| Skill not triggering | Check `data/expressions/en.json` and restart `npm start` |

> There is a non-breaking deprecation warning from `google.generativeai` on startup. It is safe to ignore — Gemini works fully. The fix when ready: `pip install google-genai` and update the import in `providers/gemini.py`.

---

## Roadmap

- [ ] Embedded voice UI in dashboard (no external playground needed)
- [ ] Hindi / multilingual support
- [ ] Face authentication on startup
- [ ] Custom "Hey Zenith" wake word
- [ ] JSON web scraping skill
- [ ] Long-term memory across sessions
- [ ] Mobile companion app
- [ ] Autonomous skill creation

---

## Quick Reference

```bash
# Start
pm2 start all

# Stop  
pm2 stop all

# Logs
pm2 logs zenith-core
pm2 logs zenith-voice

# Health check
leon check

# Dashboard
http://localhost:1337
```

---

<div align="center">

**ZENITH** — Personal AI Assistant

[github.com/MadhavaKandala/Zenith](https://github.com/MadhavaKandala/Zenith)

</div>
