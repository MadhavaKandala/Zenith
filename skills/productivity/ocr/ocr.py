#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from random import choice
import json
import re


SKILL_DIR = Path(__file__).resolve().parent
ANSWERS_PATH = SKILL_DIR / "data" / "answers" / "en.json"
CONFIG_PATH = SKILL_DIR / "config" / "config.sample.json"


def _answers() -> dict:
    with ANSWERS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _respond(key: str, replacements: dict | None = None) -> dict:
    template = choice(_answers()[key])
    for name, value in (replacements or {}).items():
        template = template.replace(f"%{name}%", str(value))
    return {"type": "end", "key": key, "speech": template}


def _extract_path(string: str) -> str | None:
    match = re.search(r"([A-Za-z]:\\[^\"']+\.(?:png|jpg|jpeg|bmp|tif|tiff))", string or "")
    return match.group(1) if match else None


def extract_text(string, entities=None):
    """Run OCR on an image path if pytesseract is available."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return _respond("dependency_missing")

    image_path = _extract_path(string or "")
    if not image_path:
        return _respond("path_missing")

    config = {}
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as file:
            config = json.load(file).get("ocr", {})
    tesseract_cmd = config.get("tesseract_cmd", "").strip()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    path = Path(image_path)
    if not path.exists():
        return _respond("not_found", {"path": image_path})

    text = pytesseract.image_to_string(Image.open(path), lang="eng").strip()
    if not text:
        return _respond("empty")
    return _respond("recognized", {"text": text})

