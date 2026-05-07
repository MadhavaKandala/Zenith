#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from random import choice
import json
import re

from tinydb import Query, TinyDB


SKILL_DIR = Path(__file__).resolve().parent
ANSWERS_PATH = SKILL_DIR / "data" / "answers" / "en.json"
DB_PATH = SKILL_DIR / "data" / "reminders.db.json"


def _answers() -> dict:
    with ANSWERS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _respond(key: str, replacements: dict | None = None) -> dict:
    template = choice(_answers()[key])
    for name, value in (replacements or {}).items():
        template = template.replace(f"%{name}%", str(value))
    return {"type": "end", "key": key, "speech": template}


def _db() -> TinyDB:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(DB_PATH)


def _extract_entity(entities: list | None, name: str) -> str | None:
    for entity in entities or []:
        if entity.get("entity") == name:
            return entity.get("sourceText") or entity.get("value")
    return None


def create_reminder(string, entities):
    """Create a new reminder."""
    reminder_text = _extract_entity(entities, "reminder_text") or string
    reminder_time = _extract_entity(entities, "time")

    reminder = {
        "text": reminder_text.strip(),
        "time": reminder_time.strip() if reminder_time else None,
        "created_at": datetime.now().isoformat(),
        "done": False,
    }

    db = _db()
    db.insert(reminder)

    text = reminder["text"]
    if reminder["time"]:
        text = f"{text} at {reminder['time']}"
    return _respond("reminder_created", {"text": text})


def list_reminders(string, entities):
    """List all active reminders."""
    db = _db()
    reminders = db.search(Query().done == False)  # noqa: E712

    if not reminders:
        return _respond("no_reminders")

    items = []
    for index, reminder in enumerate(reminders, start=1):
        label = reminder["text"]
        if reminder.get("time"):
            label = f"{label} at {reminder['time']}"
        items.append(f"{index}. {label}")

    return _respond(
        "reminders_list",
        {"count": len(reminders), "list": ", ".join(items)},
    )


def delete_reminder(string, entities):
    """Delete a reminder by index, or mark all active reminders as done."""
    db = _db()
    reminders = db.search(Query().done == False)  # noqa: E712

    if not reminders:
        return _respond("no_reminders")

    raw_id = _extract_entity(entities, "id")
    if not raw_id:
        match = re.search(r"\d+", string or "")
        raw_id = match.group(0) if match else None

    if raw_id and raw_id.isdigit():
        index = int(raw_id) - 1
        if 0 <= index < len(reminders):
            db.update({"done": True}, doc_ids=[reminders[index].doc_id])
            return _respond("reminder_deleted")

    for reminder in reminders:
        db.update({"done": True}, doc_ids=[reminder.doc_id])
    return _respond("reminder_deleted")

