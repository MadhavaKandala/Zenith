#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from random import choice

from config.loader import load_zenith_config
from providers.manager import ZenithProviderManager


SKILL_DIR = Path(__file__).resolve().parent
ANSWERS_PATH = SKILL_DIR / "data" / "answers" / "en.json"


def _answers() -> dict:
    with ANSWERS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _respond(key: str, replacements: dict | None = None) -> dict:
    template = choice(_answers()[key])
    for name, value in (replacements or {}).items():
        template = template.replace(f"%{name}%", str(value))
    return {"type": "end", "key": key, "speech": template}


async def _run_provider_chain(question: str) -> str:
    config = load_zenith_config()
    manager = ZenithProviderManager(config)
    messages = [
        {
            "role": "system",
            "content": (
                "You are Zenith, a local-first personal AI assistant inspired by JARVIS. "
                "Be concise, accurate, and practical. Address the user as sir. "
                "Answer in no more than three sentences."
            ),
        },
        {"role": "user", "content": question},
    ]
    return await manager.chat(messages)


def answer(string, entities=None):
    """Answer an open-ended question through the configured provider chain."""
    question = (string or "").strip()
    if not question:
        return _respond("error")

    try:
        answer_text = asyncio.run(_run_provider_chain(question))
    except Exception:
        return _respond("error")

    return _respond("answered", {"response": answer_text})
