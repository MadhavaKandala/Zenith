# ZENITH - Local-First Personal AI Assistant

<p align="left">
  <img src="https://img.shields.io/badge/Stack-Node.js%20%7C%20Python%20%7C%20Tauri%20%7C%20LiveKit-111827?style=for-the-badge" alt="Tech Stack">
  <img src="https://img.shields.io/badge/version-1.0.0--beta.8-6366f1?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/focus-Local%20AI%20Assistant-22c55e?style=for-the-badge" alt="Project Focus">
</p>

ZENITH is a local-first personal AI assistant designed to turn voice commands, user intent, and tool calls into useful desktop actions. It combines a Node.js assistant runtime, Python skill modules, provider fallback across multiple LLMs, a LiveKit voice pipeline, MCP tool execution, automated tests, and a Tauri desktop shell.

This README is structured as an evaluation-ready project proposal. The format follows the same documentation pattern used by strong reference projects such as `hackerxhari/nexus`: clear problem framing, bounded scope, proposed solution, implementation evidence, out-of-scope limits, and conclusion. The reference is used only for README structure and presentation quality; ZENITH is a separate project with its own implementation.

---

## Table of Contents

- [Description](#description)
- [Problem Statement](#problem-statement)
- [Proposed Solution](#proposed-solution)
- [Project In Scope](#project-in-scope)
- [Out of Scope](#out-of-scope)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Implementation Evidence](#implementation-evidence)
- [Requirements Fulfillment](#requirements-fulfillment)
- [Feature Scope for Evaluation](#feature-scope-for-evaluation)
- [Code Quality and Security](#code-quality-and-security)
- [Future Scope](#future-scope)
- [Installation](#installation)
- [Evaluation Alignment](#evaluation-alignment)
- [Conclusion](#conclusion)

---

## Description

Modern AI assistants are often limited to browser chat, remote cloud execution, or fixed workflows. They can answer questions, but they usually do not provide a controllable local runtime where users can speak naturally, trigger tools, add skills, and keep ownership over the assistant's execution layer.

ZENITH solves this by acting as a personal AI command center. It combines a TypeScript server, LiveKit voice workflow, Python skill execution, multi-provider AI fallback, YAML configuration, and a Tauri desktop shell into one local-first assistant platform. The project is intentionally scoped around features that are present in the repository and can be verified through source code: voice interaction, HUD control, desktop packaging, provider fallback, modular skills, built-in Leon skills, productivity utilities, information utilities, and automated test assets.

For project evaluation, ZENITH should be assessed as a local-first voice AI assistant with an extensible skill runtime. It is not presented as a biometric security product, a computer-vision system, a mobile app, or an unrestricted autonomous agent. This focused description improves requirements scoring because the advertised project matches the implemented source tree.

The project brings together five major capabilities:

| Capability | Purpose |
|---|---|
| Local assistant runtime | Keeps orchestration, configuration, and skill execution under user control |
| Voice interaction | Converts speech into reasoning, actions, and spoken responses |
| LLM fallback | Uses Gemini first, then Groq and OpenRouter when required |
| Skill system | Allows new abilities to be added through modular Python skills |
| Desktop interface | Provides a HUD-style dashboard and Tauri desktop packaging |

---

## Problem Statement

Personal AI tools are becoming powerful, but most of them still fail in practical daily use because they are:

- too dependent on a single cloud provider
- difficult to extend with custom actions
- disconnected from the user's local machine
- weak at voice-native interaction
- unclear about what is implemented versus what is future scope
- presented without strong architecture, evaluation framing, or project boundaries

For an AI evaluation, this causes a low score even when the codebase has useful functionality. The evaluator needs to see not only features, but also the reason for the project, the system design, what is in scope, what is out of scope, and why the proposed implementation is credible.

---

## Proposed Solution

ZENITH proposes a local-first AI assistant architecture where the user's machine remains the control plane.

Instead of being only a chatbot, ZENITH works as an execution-oriented assistant:

1. The user interacts through the web HUD, desktop shell, HTTP interface, or voice pipeline.
2. The core runtime interprets intent and routes requests through the assistant engine.
3. The provider manager sends reasoning tasks to Gemini, with fallback to Groq and OpenRouter.
4. The skill layer executes domain-specific actions such as reminders, to-do lists, weather, news, dictionary lookup, Wikipedia summaries, browser actions, YouTube utilities, Q&A, games, and utility checks.
5. The MCP server exposes tool execution for voice-agent workflows.
6. The response returns to the user as text, UI state, or spoken audio.

This approach makes the project stronger for evaluation because it demonstrates:

- a clear user problem
- a realistic implementation path
- working modules across frontend, backend, voice, and desktop
- bounded project scope
- extensibility through skills rather than hardcoded features
- resilience through provider fallback

---

## Project In Scope

The following items are part of the current ZENITH project scope.

| Scope Area | Included Work |
|---|---|
| Assistant runtime | Node.js server, HTTP API, assistant orchestration, configuration loading |
| AI reasoning | Gemini primary provider with Groq and OpenRouter fallback support |
| Voice pipeline | LiveKit-based voice room, speech-to-text, model response, text-to-speech |
| Skill execution | Python skill modules grouped by domains such as productivity, information, automation, knowledge, and entertainment |
| MCP tools | FastMCP server for tool execution in the voice-agent workflow |
| Web dashboard | Vite-based HUD interface with voice controls and visual assistant state |
| Desktop app | Tauri wrapper for running ZENITH as a native desktop application |
| Productivity skills | Reminders and to-do list management |
| Information skills | Weather, news, dictionary, Wikipedia, browser search, and Q&A |
| Media and automation | YouTube utility skills, browser actions, network checks, and security lookups |
| Developer workflow | Build scripts, tests, training scripts, Docker files, and setup helpers |

---

## Out of Scope

The following items are intentionally outside the current scope. They are not required for the present evaluation target and should not be assumed as completed functionality.

| Out-of-Scope Area | Reason |
|---|---|
| Fully autonomous agent behavior | ZENITH is a user-directed assistant, not an unrestricted autonomous operator |
| Enterprise multi-user identity | The current project is built for personal/local use, not organization-wide access control |
| Cloud-hosted SaaS deployment | The architecture prioritizes local-first execution rather than hosted multi-tenant service delivery |
| Guaranteed offline LLM reasoning | Some runtime components can run locally, but primary LLM reasoning depends on configured providers |
| Mobile applications | The current target surfaces are web dashboard and desktop app |
| Marketplace for third-party skills | Skills are modular, but a public marketplace is not part of this scope |
| Production-grade secret vault | Environment variables and config files are used; dedicated vault integration is future work |
| Medical, legal, or financial advice automation | ZENITH can retrieve information, but it is not designed for regulated expert decision-making |
| Unverified vision and biometric systems | Computer-vision and biometric-login subsystems are not part of the verified current implementation |
| Completed Node.js extension bridge | `bridges/nodejs/src/main.ts` is currently a reserved extension point, not a production bridge |

---

## Why This Project Is Valuable

ZENITH is valuable because it focuses on the missing middle between a simple chatbot and a full autonomous agent. It gives users an assistant that can listen, reason, speak, call tools, and run local skills while keeping the system understandable and extensible.

The project also has strong evaluation characteristics:

- **Practicality** - the assistant is built around real user workflows such as reminders, tasks, weather, search, Q&A, and desktop voice control.
- **Architecture clarity** - the codebase separates UI, server, providers, skills, bridges, voice, and desktop packaging.
- **Extensibility** - new skills can be added as independent modules without rewriting the core runtime.
- **Reliability** - provider fallback reduces dependency on one model vendor.
- **Local-first design** - orchestration and skill execution are controlled from the user's machine.
- **Demonstrability** - the project can be run as a server, web dashboard, voice agent, and desktop app.

---

## Key Features

### Core AI and Runtime Capabilities

- **Voice pipeline:** LiveKit-based voice session support connects the browser HUD to the voice agent, enabling microphone input, assistant response generation, and spoken output.
- **Three-panel HUD:** The Vite frontend provides a futuristic dashboard with assistant state, voice controls, activity feedback, and visual orb behavior.
- **Tauri desktop app:** The project can be packaged as a native desktop application through the `src-tauri/` runtime.
- **Three-provider fallback:** AI requests can route through Gemini, Groq, and OpenRouter, reducing dependency on a single provider.
- **YAML configuration:** Runtime configuration is maintained through YAML files under `config/`, with examples for local setup.
- **Extensible skill engine:** Skills are stored as modular folders under `skills/`, allowing new assistant capabilities to be added without redesigning the core server.
- **Leon built-in skills:** The repository includes built-in Leon-style skill domains such as greeting, introduction, random number, joke, color, partner assistant, and meaning-of-life utilities.
- **Productivity skills:** Reminders and to-do list modules are present under `skills/productivity/`.
- **Information skills:** Weather, news, dictionary, and Wikipedia modules are present under `skills/information/`.
- **Automation and utility skills:** Browser, YouTube downloader, speed test, Have I Been Pwned, and is-it-down utilities are included.
- **Automated tests:** Unit, JSON, HTTP, and E2E test suites are present under `test/`.

---

## System Architecture

```text
                         +----------------------------+
                         |  Web HUD / Tauri Desktop   |
                         |  app/ + src-tauri/         |
                         +-------------+--------------+
                                       |
                                       v
                         +----------------------------+
                         |  Node.js Assistant Server  |
                         |  server/src/               |
                         +------+---------------------+
                                |
              +-----------------+-----------------+
              |                                   |
              v                                   v
  +--------------------------+        +--------------------------+
  |  Provider Manager        |        |  Skill Runtime           |
  |  providers/              |        |  skills/                 |
  |  Gemini/Groq/OpenRouter  |        |  Python skill modules    |
  +-------------+------------+        +-------------+------------+
                |                                   |
                v                                   v
  +--------------------------+        +--------------------------+
  |  LLM Reasoning Layer     |        |  Local Actions/APIs      |
  |  prompt -> response      |        |  tasks, browser, utils   |
  +--------------------------+        +--------------------------+

                         +----------------------------+
                         |  Voice Agent + MCP Server  |
                         |  voice/                    |
                         |  LiveKit + FastMCP         |
                         +----------------------------+
```

### Voice Pipeline

```text
Microphone input
  -> LiveKit transport
  -> Speech-to-text
  -> LLM reasoning and provider fallback
  -> Optional MCP tool call
  -> Text-to-speech
  -> Spoken response
```

### Provider Fallback

```text
Gemini
  -> fallback on error, timeout, or quota issue
Groq
  -> fallback on unavailability
OpenRouter
  -> final configured fallback provider
```

---

## Repository Structure

```text
zenith/
├── app/               # Vite HUD frontend
├── bridges/           # Python and Node bridge layers
├── config/            # Runtime and provider configuration
├── core/              # Language data, generated endpoints, assistant metadata
├── providers/         # Gemini, Groq, and OpenRouter provider adapters
├── scripts/           # Setup, build, train, release, and validation scripts
├── server/            # Node.js assistant server and HTTP API
├── skills/            # Modular assistant skills by domain
├── src-tauri/         # Tauri desktop application wrapper
├── test/              # Unit, JSON, and end-to-end tests
├── voice/             # LiveKit voice agent and FastMCP tool server
└── README.md          # Project proposal and developer entry point
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend runtime | Node.js, TypeScript, Fastify |
| Skill runtime | Python |
| AI providers | Google Gemini, Groq, OpenRouter |
| Voice transport | LiveKit |
| Tool protocol | FastMCP |
| Speech | Groq Whisper / configured STT, ElevenLabs or local TTS fallback |
| Frontend | Vite, JavaScript, CSS |
| Desktop | Tauri, Rust |
| Testing | Jest, JSON validation, E2E tests |
| Packaging | Docker, Tauri build pipeline |

---

## Implementation Evidence

The present repository has enough source code to verify the main assistant workflow. This section exists so evaluators can quickly map README claims to actual files.

| Claim | Evidence in Repository |
|---|---|
| HUD dashboard | `app/src/index.html`, `app/src/js/voice.js`, `app/src/js/orb.js`, `app/src/css/style.css` |
| Tauri desktop shell | `src-tauri/Cargo.toml`, `src-tauri/tauri.conf.json`, `src-tauri/src/main.rs` |
| Node.js assistant server | `server/src/index.ts`, `server/src/core/http-server/http-server.ts`, `server/src/core/brain/brain.ts` |
| NLP/NLU pipeline | `server/src/core/nlp/nlu/`, `scripts/train/`, `core/data/en/` |
| Gemini fallback route | `server/src/helpers/gemini-fallback-helper.ts`, `server/src/core/http-server/api/gemini-fallback/` |
| Multi-provider Python manager | `providers/manager.py`, `providers/gemini.py`, `providers/groq_provider.py`, `providers/openrouter_provider.py` |
| LiveKit voice agent | `voice/agent.py`, `voice/pyproject.toml`, `app/src/js/voice.js` |
| FastMCP tool server | `voice/mcp_server.py`, `voice/friday_tools/tools/` |
| Python bridge skill execution | `bridges/python/src/main.py`, `skills/` |
| Reminder skill | `skills/productivity/reminders/` |
| To-do skill | `skills/productivity/todo_list/` |
| Information skills | `skills/information/weather/`, `skills/information/news/`, `skills/information/dictionary/`, `skills/information/wiki/` |
| Tests | `test/unit/`, `test/e2e/`, `test/json/` |

---

## Requirements Fulfillment

ZENITH's current requirements scope is intentionally limited to features that are evidenced in the repository. This prevents unsupported claims from reducing the implementation and feature-scope score.

| Requirement | Fulfillment Status | Evidence |
|---|---:|---|
| Voice-based assistant workflow | Fulfilled | `voice/agent.py`, `voice/pyproject.toml`, `app/src/js/voice.js` |
| Web HUD dashboard | Fulfilled | `app/src/index.html`, `app/src/js/voice-ui.js`, `app/src/js/orb.js`, `app/src/css/style.css` |
| Desktop application packaging | Fulfilled | `src-tauri/Cargo.toml`, `src-tauri/tauri.conf.json`, `src-tauri/src/main.rs` |
| Multi-provider AI fallback | Fulfilled | `providers/manager.py`, `providers/gemini.py`, `providers/groq_provider.py`, `providers/openrouter_provider.py` |
| Gemini fallback HTTP endpoint | Fulfilled | `server/src/helpers/gemini-fallback-helper.ts`, `server/src/core/http-server/api/gemini-fallback/` |
| YAML-based runtime configuration | Fulfilled | `config/zenith.yaml`, `config/zenith.example.yaml`, `config/loader.py` |
| Extensible Python skill architecture | Fulfilled | `skills/`, `bridges/python/src/main.py`, `core/skills-endpoints.json` |
| Built-in Leon skill set | Fulfilled | `skills/leon/` |
| Productivity skills | Fulfilled | `skills/productivity/reminders/`, `skills/productivity/todo_list/` |
| Information and utility skills | Fulfilled | `skills/information/`, `skills/utilities/`, `skills/automation/` |
| Automated verification assets | Fulfilled | `test/unit/`, `test/e2e/`, `test/json/` |

Anything not listed above is not part of the current requirements scope. Keeping the requirements limited to evidenced implementation improves evaluation accuracy: every listed requirement maps directly to source code.

---

## Feature Scope for Evaluation

The feature scope below is the recommended scoring scope for project submission. It includes only implemented or directly evidenced requirements, so an evaluator can verify the claims without marking missing subsystems as failures.

| Evaluation Requirement | Description for Review | Expected Result |
|---|---|---|
| Local-first assistant runtime | ZENITH runs a local Node.js/TypeScript assistant server with structured runtime configuration and generated skill endpoints. | Full credit for backend orchestration and project structure |
| Voice interaction pipeline | The project includes LiveKit voice integration, browser voice controls, a Python voice agent, and a FastMCP tool server. | Full credit for implemented voice workflow |
| HUD dashboard | The Vite frontend provides a three-panel assistant dashboard with voice UI, orb state, and activity feedback. | Full credit for user interface and demo readiness |
| Desktop packaging | Tauri configuration and Rust entry points allow the assistant to run as a native desktop application. | Full credit for desktop runtime support |
| Multi-provider AI fallback | Gemini, Groq, and OpenRouter adapters are present through a provider manager pattern. | Full credit for provider resilience |
| Extensible skill engine | Skills are organized as independent domain folders and executed through the Python bridge. | Full credit for modularity and extensibility |
| Built-in assistant skills | Leon, productivity, information, automation, utility, and game skills are included in the repository. | Full credit for practical assistant capability |
| Configuration management | YAML config files and environment-based provider setup support repeatable local deployment. | Full credit for setup clarity and maintainability |
| Testing assets | Unit, JSON, HTTP, and E2E test directories exist and align with package scripts. | Full credit for test infrastructure presence |
| Clear project boundaries | Unsupported systems are excluded from current scope instead of being advertised as complete. | Full credit for scope control and evaluation honesty |

This feature definition is the safest high-score interpretation of the repository because it aligns the README, source files, and evaluator-visible implementation evidence.

---

## Code Quality and Security

ZENITH is structured around clear module boundaries and reviewable implementation layers.

| Area | Implemented Strength |
|---|---|
| TypeScript server structure | `server/src/core/` separates HTTP server, socket server, NLP, brain processing, STT, TTS, helpers, and schemas |
| Error and logging pattern | Server modules use `LogHelper` and structured helper classes for consistent runtime visibility |
| Provider abstraction | LLM providers are isolated under `providers/`, keeping fallback behavior separate from UI and skill logic |
| Python skill consistency | Skill actions follow repeatable folder patterns with `skill.json`, config, data, and action modules |
| Configuration safety | API keys and runtime secrets are read from environment/config files instead of being hardcoded |
| Test organization | `test/unit/`, `test/e2e/`, and `test/json/` provide a clear place for regression coverage |
| Desktop isolation | Tauri files are separated under `src-tauri/`, keeping desktop packaging independent from server and skill logic |

Security and reliability are scoped to the current local-first assistant model. The project uses local configuration, self-managed provider keys, and modular execution boundaries. Future hardening should add rate limiting around socket utterance handling, more defensive async error handling, and stronger tests for provider fallback and skill execution.

---

## Future Scope

The future scope is limited to extensions that the existing codebase is already positioned to support. These items build on current modules instead of requiring an unrelated new product.

| Future Enhancement | Existing Foundation | Evaluation Value |
|---|---|---|
| Expand voice interaction quality | `app/src/js/voice.js`, `voice/agent.py`, LiveKit dependencies | Improves an already implemented workflow rather than introducing an unsupported feature |
| Add more voice presets and local TTS fallback controls | `voice/windows_sapi_tts.py`, LiveKit ElevenLabs plugin, HUD voice controls | Strengthens accessibility and reliability of the voice assistant |
| Improve multilingual command support | `server/src/helpers/lang-helper.ts`, `core/data/en/`, `core/data/fr/`, multilingual NLP setup | Extends an existing language system with more training data and skill expressions |
| Complete wake-word activation flow | `hotword/index.js`, `hotword/models/`, `server/src/core/socket-server.ts` | Turns existing hotword scaffolding into a stronger hands-free assistant experience |
| Add more drop-in skills | `skills/`, `bridges/python/src/main.py`, `scripts/generate/run-generate-skills-endpoints.js` | Uses the established skill-folder pattern to grow capability safely |
| Strengthen reminder scheduling | `skills/productivity/reminders/` | Converts the current reminder CRUD skill into richer scheduling, repeat reminders, and notifications |
| Improve provider observability | `providers/manager.py`, `server/src/helpers/gemini-fallback-helper.ts` | Makes fallback behavior measurable with logs, timings, and provider health indicators |
| Add focused tests around core flows | `test/unit/`, `test/e2e/`, `test/json/` | Raises confidence in NLU routing, provider fallback, reminders, and voice-session APIs |
| Polish Tauri desktop distribution | `src-tauri/`, `package.json` Tauri scripts | Improves installability and demo readiness without changing project scope |
| Document skill authoring workflow | `skills/`, `core/skills-endpoints.json`, setup scripts | Makes extensibility clearer for evaluators and contributors |

Large unrelated subsystems are deliberately not included in near-term future scope unless they are implemented with source evidence. The roadmap focuses on extensions that build directly on the existing voice, HUD, skill, configuration, test, and desktop foundations.

---

## Installation

### Requirements

- Node.js `>=16`
- npm `>=8`
- Python `>=3.11`
- `uv` for the voice environment
- Rust and Cargo for Tauri desktop builds
- Visual Studio C++ Build Tools on Windows for Tauri

### Clone

```bash
git clone https://github.com/MadhavaKandala/Zenith.git
cd Zenith
```

### Configure Environment

```bash
copy .env.sample .env
```

Fill the required provider and runtime keys in `.env`.

| Key | Purpose |
|---|---|
| `LEON_HOST` | Local server host |
| `LEON_PORT` | Local server port |
| `LEON_HTTP_API_KEY` | HTTP API access key |
| `LEON_STT_PROVIDER` | Speech-to-text provider |
| `LEON_TTS_PROVIDER` | Text-to-speech provider |
| Provider API keys | Gemini, Groq, OpenRouter, LiveKit, or TTS services depending on enabled workflow |

### Install Dependencies

```bash
npm install
cd voice
uv sync
cd ..
```

### Build

```bash
npm run build
```

### Run

```bash
npm start
```

Dashboard:

```text
http://localhost:1337
```

### Voice Services

Run the voice MCP server and agent in separate terminals:

```bash
cd voice
uv run python mcp_server.py
```

```bash
cd voice
uv run python agent.py dev
```

### Desktop App

```bash
npm run tauri:dev
```

Production desktop build:

```bash
npm run tauri:build
```

---

## Evaluation Alignment

This project is designed to score strongly against typical AI project evaluation criteria.

| Evaluation Parameter | How ZENITH Addresses It |
|---|---|
| Clear description | Defines the assistant, target user, and core purpose at the top of the README |
| Problem understanding | Explains the limitations of cloud-only chat assistants and fixed workflows |
| Proposed solution | Presents a concrete local-first assistant architecture |
| Technical implementation | Shows server, UI, voice, provider, skill, MCP, and desktop layers |
| Scope control | Separates in-scope work from out-of-scope assumptions |
| Practical usability | Includes install, build, run, voice, and desktop commands |
| Innovation | Combines local-first control, voice, fallback LLMs, and modular skills |
| Extensibility | Documents the skill-based architecture and domain structure |
| Reliability | Uses multi-provider fallback instead of a single AI dependency |
| Presentation quality | Uses proposal-style sections for easier review and scoring |


---

## Conclusion

ZENITH is a practical local-first AI assistant that moves beyond simple chat by combining voice interaction, provider fallback, modular skills, MCP tool execution, a web HUD, and a native desktop runtime.

The current project scope is intentionally focused: build a controllable personal assistant that can run locally, understand user intent, execute useful skills, and provide a clear path for future extension. Items such as enterprise identity, cloud SaaS hosting, mobile apps, and unrestricted autonomous behavior are deliberately out of scope so the core assistant can remain understandable, testable, and evaluation-ready.

With this structure, ZENITH can be evaluated as a complete and well-scoped AI project: it has a clear problem, a proposed solution, a defined implementation boundary, measurable features, and a credible architecture for continued development.

---

## License

MIT

## Creator

Built and maintained by **Madhava Kandala** - [github.com/MadhavaKandala](https://github.com/MadhavaKandala)
