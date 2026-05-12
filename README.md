# Zenith

Zenith is a local-first personal AI assistant built around a four-runtime architecture:

1. `Node.js + TypeScript` orchestrator on port `1337`
2. `Python` skill bridge and NLP support on port `1342`
3. `LiveKit Agents + FastMCP` voice runtime in `voice/`
4. `Tauri + Rust` desktop shell in `src-tauri/`

The project is designed for developer ownership: offline intent routing stays local, Python skills are drop-in folders, the desktop UI is bundled as a native Windows app, and the cloud-facing AI providers are user-selected instead of vendor-locked.

## What Zenith Supports

- Offline NLU with trained NLP.js model files
- LiveKit WebRTC voice sessions with Groq Whisper STT, Gemini LLM, and Google Cloud TTS
- Gemini -> Groq -> OpenRouter fallback chain for open-ended Q&A
- Dynamic Python skill loading from the `skills/` folder with no core edits
- JARVIS-style three-panel HUD with animated orb, particle background, scanline overlay, and live activity feed
- Browser automation via `webbrowser` and Playwright-backed helpers
- OCR through `pytesseract` and Tesseract
- Persistent per-skill storage through TinyDB
- Real-time tool execution events over WebSocket
- Native desktop packaging through Tauri
- REST endpoints under `/api/v1/`

## Supported Skill Set

Zenith currently exposes 13 supported skills through the assistant surface:

1. `productivity/reminders`
2. `productivity/todo_list`
3. `information/weather`
4. `information/news`
5. `information/wiki`
6. `information/dictionary`
7. `knowledge/qa`
8. `automation/chrome`
9. `automation/desktop_control`
10. `utilities/ocr`
11. `leon/joke`
12. `games/guess_the_number`
13. `games/rochambeau`

The canonical list is stored in [config/active_skills.json](/C:/Users/nnssp/Desktop/zenith3.0/Zenith/config/active_skills.json).

## Architecture

### 1. Node.js Orchestrator

- Entry point: [server/src/index.ts](/C:/Users/nnssp/Desktop/zenith3.0/Zenith/server/src/index.ts)
- Serves the HUD and REST API
- Loads the offline NLP.js models
- Routes matched intents to the Python bridge
- Uses Gemini fallback for unmatched text queries
- Broadcasts live execution events over Socket.IO

### 2. Python Skill Bridge

- Entry point: [bridges/python/src/main.py](/C:/Users/nnssp/Desktop/zenith3.0/Zenith/bridges/python/src/main.py)
- Imports skills dynamically from `skills.<domain>.<skill>.src.actions.<action>`
- Keeps the core closed for modification and the skill surface open for extension

### 3. Voice Runtime

- Voice agent: [voice/agent.py](/C:/Users/nnssp/Desktop/zenith3.0/Zenith/voice/agent.py)
- MCP tool server: [voice/mcp_server.py](/C:/Users/nnssp/Desktop/zenith3.0/Zenith/voice/mcp_server.py)
- Uses Groq Whisper for STT
- Uses Gemini as the primary LiveKit LLM
- Uses Google Cloud TTS when credentials are present, with Windows SAPI as a local fallback
- Exposes a provider-chain reasoning tool for longer-form answers

### 4. Desktop Shell

- Tauri config: [src-tauri/tauri.conf.json](/C:/Users/nnssp/Desktop/zenith3.0/Zenith/src-tauri/tauri.conf.json)
- Rust bootstrap: [src-tauri/src/lib.rs](/C:/Users/nnssp/Desktop/zenith3.0/Zenith/src-tauri/src/lib.rs)

## Provider Ownership

Provider selection is implemented in [providers/manager.py](/C:/Users/nnssp/Desktop/zenith3.0/Zenith/providers/manager.py).

Order:

1. Gemini
2. Groq
3. OpenRouter

If one provider raises an exception, Zenith advances to the next provider without interrupting the user-facing request.

## Configuration

Primary YAML config:

- [config/zenith.yaml](/C:/Users/nnssp/Desktop/zenith3.0/Zenith/config/zenith.yaml)
- [config/zenith.example.yaml](/C:/Users/nnssp/Desktop/zenith3.0/Zenith/config/zenith.example.yaml)

Common environment variables:

- `LEON_HOST`
- `LEON_PORT`
- `LEON_PY_TCP_SERVER_HOST`
- `LEON_PY_TCP_SERVER_PORT`
- `GOOGLE_API_KEY`
- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `GOOGLE_APPLICATION_CREDENTIALS`

## Run

Install dependencies:

```bash
npm install
```

Train NLP models:

```bash
npm run train
```

Start the web stack:

```bash
npm run build
npm start
```

Run the Tauri shell:

```bash
npm run tauri:dev
```

Run the voice worker:

```bash
cd voice
python agent.py
```

Run the FastMCP tool server:

```bash
cd voice
python mcp_server.py
```

## Out of Scope

These are intentionally not part of the supported Zenith surface:

- Startup face-auth gate
- Multilingual Hindi skill packs
- Custom wake-word migration work
- Mobile companion app
- Autonomous skill file generation
- Multi-user profile isolation
- Cloud-hosted Zenith deployment
- Node.js skill bridge
- Socket.IO rate limiting

Those surfaces have been removed from the active product story and should not be treated as supported features.

## Notes on Privacy

Zenith keeps orchestration, NLU classification, skill execution, and desktop automation local. When you configure Gemini, Groq, OpenRouter, LiveKit Cloud, Google Cloud TTS, NewsAPI, or OpenWeather, the relevant requests go directly to those user-selected providers. Zenith does not depend on a hidden assistant-specific vendor backend.
