#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path
from random import choice
import json
import re

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


def _extract_location(string: str) -> str:
    match = re.search(r"(?:in|for|at)\s+(.+)$", string, re.IGNORECASE)
    return match.group(1).strip() if match else "auto:ip"

def _get_api_key() -> str:
    api_key = ""
    try:
        import utils
        api_key = utils.config("api_key")
    except Exception:
        api_key = ""

    return api_key or os.getenv("OPENWEATHER_API_KEY", "")


def get_weather(string, entities):
    """Return the current weather for a place or the caller IP location."""
    location = _extract_location(string or "")
    api_key = _get_api_key()

    try:
        if api_key:
            query = "Hyderabad" if location == "auto:ip" else location
            data = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": query, "appid": api_key, "units": "metric"},
                timeout=15,
            ).json()
            summary = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            area = data["name"]
            country = data["sys"]["country"]
        else:
            data = requests.get(f"https://wttr.in/{location}?format=j1", timeout=15).json()
            current = data["current_condition"][0]
            nearest = data.get("nearest_area", [{}])[0]
            area = nearest.get("areaName", [{"value": location}])[0]["value"]
            country = nearest.get("country", [{"value": ""}])[0]["value"]
            summary = current["weatherDesc"][0]["value"]
            temperature = current["temp_C"]
            humidity = current["humidity"]
    except (KeyError, IndexError, ValueError, TypeError, requests.RequestException):
        return _respond("error", {"location": location})

    label = area if not country else f"{area}, {country}"
    return _respond(
        "weather",
        {
            "location": label,
            "summary": summary,
            "temperature": temperature,
            "humidity": humidity
        }
    )
