#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from random import choice
import json
import os

import requests


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


def answer(string, entities):
    """Answer any question using Gemini."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return _respond("missing_api_key")

    prompt = (
        "You are Zenith, a personal AI assistant in the style of JARVIS from Iron Man.\n"
        "Answer this question concisely and helpfully (2-3 sentences max for voice output):\n\n"
        f"{string}"
    )
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, json=payload, timeout=30)
    data = response.json()
    try:
        answer_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError):
        return _respond("error")

    return _respond("answered", {"response": answer_text})

