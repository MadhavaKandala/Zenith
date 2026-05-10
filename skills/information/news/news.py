#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from random import choice
import json
from xml.etree import ElementTree

import requests


SKILL_DIR = Path(__file__).resolve().parent
ANSWERS_PATH = SKILL_DIR / "data" / "answers" / "en.json"
CONFIG_PATH = SKILL_DIR / "config" / "config.json"
SAMPLE_CONFIG_PATH = SKILL_DIR / "config" / "config.sample.json"


def _answers() -> dict:
    with ANSWERS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _config() -> dict:
    path = CONFIG_PATH if CONFIG_PATH.exists() else SAMPLE_CONFIG_PATH
    with path.open("r", encoding="utf-8") as file:
        return json.load(file).get("news", {})


def _respond(key: str, replacements: dict | None = None) -> dict:
    template = choice(_answers()[key])
    for name, value in (replacements or {}).items():
        template = template.replace(f"%{name}%", str(value))
    return {"type": "end", "key": key, "speech": template}


def get_headlines(string, entities):
    """Fetch and speak today's headlines."""
    config = _config()
    api_key = config.get("newsapi_key", "")
    max_articles = config.get("max_articles") or 5

    headlines = []
    if api_key:
        url = (
            "https://newsapi.org/v2/top-headlines"
            f"?country=in&apiKey={api_key}&pageSize={max_articles}"
        )
        response = requests.get(url, timeout=15)
        data = response.json()
        if data.get("status") == "ok":
            headlines = [
                article["title"]
                for article in data.get("articles", [])
                if article.get("title")
            ]

    if not headlines:
        response = requests.get(
            "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
            timeout=15,
        )
        root = ElementTree.fromstring(response.content)
        headlines = [
            item.findtext("title", "").strip()
            for item in root.findall(".//item")[: int(max_articles)]
        ]
        headlines = [headline for headline in headlines if headline]

    if not headlines:
        return _respond("fetch_error")

    result = ". ".join(headlines)
    return _respond("headlines", {"news": result})
