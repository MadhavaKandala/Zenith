"""
Zenith Global Memory Abstraction Layer
=======================================
Provides a unified memory interface for both per-skill TinyDB storage
and a global conversation/knowledge vault. This allows long-term memory
persistence beyond individual skill databases.

Supports:
  - Chat history with configurable limits
  - Long-term knowledge vault (key-value facts)
  - Per-skill isolated storage
  - SQLite and TinyDB backends

Usage:
    from core.memory import ZenithMemory
    mem = ZenithMemory()
    mem.store_chat("user", "What's the weather?")
    mem.store_fact("user_name", "Madhava")
    history = mem.get_chat_history(limit=10)
    name = mem.recall_fact("user_name")
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("zenith.memory")

try:
    from tinydb import TinyDB, Query

    _TINYDB_AVAILABLE = True
except ImportError:
    _TINYDB_AVAILABLE = False


class ZenithMemory:
    """
    Unified memory abstraction for Zenith.

    Supports both TinyDB (default) and SQLite backends.
    Provides chat history, long-term fact storage, and per-skill namespaces.
    """

    DEFAULT_DB_DIR = os.path.join(os.path.expanduser("~"), ".zenith")

    def __init__(
        self,
        db_type: str = "tinydb",
        db_path: Optional[str] = None,
        chat_history_limit: int = 100,
    ):
        """
        Initialize the memory system.

        Args:
            db_type: Backend type ('tinydb' or 'sqlite').
            db_path: Path to the database file. Auto-generated if None.
            chat_history_limit: Maximum chat messages to retain.
        """
        self.db_type = db_type
        self.chat_history_limit = chat_history_limit
        self._db_dir = Path(self.DEFAULT_DB_DIR)
        self._db_dir.mkdir(parents=True, exist_ok=True)

        if db_path:
            self._db_path = Path(db_path)
        else:
            ext = ".json" if db_type == "tinydb" else ".db"
            self._db_path = self._db_dir / f"zenith_memory{ext}"

        self._knowledge_cache = {}
        self._skill_cache = {}

        # Initialize backend
        if db_type == "tinydb":
            if not _TINYDB_AVAILABLE:
                raise RuntimeError("TinyDB is not installed. Install with: pip install tinydb")
            self._db = TinyDB(str(self._db_path))
            self._chat_table = self._db.table("chat_history")
            self._facts_table = self._db.table("knowledge_vault")
            self._skills_table = self._db.table("skill_data")
        elif db_type == "sqlite":
            self._conn = sqlite3.connect(str(self._db_path))
            self._init_sqlite_schema()
        else:
            raise ValueError(f"Unsupported db_type: {db_type}. Use 'tinydb' or 'sqlite'.")

        logger.info(
            "Memory initialized: type=%s, path=%s, limit=%d",
            db_type,
            self._db_path,
            chat_history_limit,
        )

    def _init_sqlite_schema(self) -> None:
        """Create SQLite tables if they don't exist."""
        cursor = self._conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS knowledge_vault (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                timestamp REAL NOT NULL,
                source TEXT DEFAULT 'user'
            );

            CREATE TABLE IF NOT EXISTS skill_data (
                skill_name TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                timestamp REAL NOT NULL,
                PRIMARY KEY (skill_name, key)
            );

            CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_history(timestamp);
            CREATE INDEX IF NOT EXISTS idx_skill_name ON skill_data(skill_name);
            """
        )
        self._conn.commit()

    # ── Chat History ───────────────────────────────────────────────────

    def store_chat(self, role: str, content: str, metadata: Optional[dict] = None) -> None:
        """
        Store a chat message in history.

        Args:
            role: 'user' or 'assistant'.
            content: Message content.
            metadata: Optional metadata dict.
        """
        entry = {
            "timestamp": time.time(),
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }

        if self.db_type == "tinydb":
            self._chat_table.insert(entry)
            self._enforce_chat_limit_tinydb()
        else:
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (timestamp, role, content, metadata) VALUES (?, ?, ?, ?)",
                (entry["timestamp"], role, content, json.dumps(entry["metadata"])),
            )
            self._conn.commit()
            self._enforce_chat_limit_sqlite()

    def get_chat_history(self, limit: Optional[int] = None) -> list[dict]:
        """
        Retrieve chat history, most recent first.

        Args:
            limit: Max messages to return (defaults to chat_history_limit).

        Returns:
            List of chat message dicts.
        """
        limit = limit or self.chat_history_limit

        if self.db_type == "tinydb":
            all_msgs = self._chat_table.all()
            sorted_msgs = sorted(all_msgs, key=lambda x: x.get("timestamp", 0), reverse=True)
            return sorted_msgs[:limit]
        else:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT timestamp, role, content, metadata FROM chat_history ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return [
                {
                    "timestamp": row[0],
                    "role": row[1],
                    "content": row[2],
                    "metadata": json.loads(row[3]),
                }
                for row in cursor.fetchall()
            ]

    def _enforce_chat_limit_tinydb(self) -> None:
        """Trim chat history to the configured limit."""
        if len(self._chat_table) <= self.chat_history_limit:
            return
            
        logger.warning("TinyDB memory constraint: reading entire chat table for pruning. Use SQLite for large histories.")
        all_msgs = self._chat_table.all()
        sorted_msgs = sorted(all_msgs, key=lambda x: x.get("timestamp", 0))
        excess = len(all_msgs) - self.chat_history_limit
        self._chat_table.remove(doc_ids=[msg.doc_id for msg in sorted_msgs[:excess]])

    def _enforce_chat_limit_sqlite(self) -> None:
        """Trim chat history to the configured limit."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chat_history")
        count = cursor.fetchone()[0]
        if count > self.chat_history_limit:
            excess = count - self.chat_history_limit
            cursor.execute(
                "DELETE FROM chat_history WHERE id IN (SELECT id FROM chat_history ORDER BY timestamp ASC LIMIT ?)",
                (excess,),
            )
            self._conn.commit()

    def clear_chat_history(self) -> None:
        """Clear all chat history."""
        if self.db_type == "tinydb":
            self._chat_table.truncate()
        else:
            self._conn.execute("DELETE FROM chat_history")
            self._conn.commit()
        logger.info("Chat history cleared")

    # ── Knowledge Vault (Long-Term Memory) ─────────────────────────────

    def store_fact(self, key: str, value: Any, source: str = "user") -> None:
        """
        Store a fact in the long-term knowledge vault.

        Args:
            key: Fact identifier (e.g., 'user_name', 'favorite_color').
            value: The fact value.
            source: Origin of the fact ('user', 'inference', 'skill').
        """
        self._knowledge_cache[key] = value
        
        if self.db_type == "tinydb":
            Fact = Query()
            self._facts_table.upsert(
                {"key": key, "value": value, "timestamp": time.time(), "source": source},
                Fact.key == key,
            )
        else:
            self._conn.execute(
                "INSERT OR REPLACE INTO knowledge_vault (key, value, timestamp, source) VALUES (?, ?, ?, ?)",
                (key, json.dumps(value) if not isinstance(value, str) else value, time.time(), source),
            )
            self._conn.commit()

        logger.info("Stored fact: %s = %s (source: %s)", key, value, source)

    def recall_fact(self, key: str) -> Optional[Any]:
        """
        Recall a fact from the knowledge vault.

        Args:
            key: Fact identifier.

        Returns:
            The fact value, or None if not found.
        """
        if key in self._knowledge_cache:
            return self._knowledge_cache[key]
            
        result_val = None
        if self.db_type == "tinydb":
            Fact = Query()
            result = self._facts_table.search(Fact.key == key)
            result_val = result[0]["value"] if result else None
        else:
            cursor = self._conn.cursor()
            cursor.execute("SELECT value FROM knowledge_vault WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    result_val = json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    result_val = row[0]
                    
        self._knowledge_cache[key] = result_val
        return result_val

    def get_all_facts(self) -> dict[str, Any]:
        """Return all stored facts as a dictionary."""
        if self.db_type == "tinydb":
            return {item["key"]: item["value"] for item in self._facts_table.all()}
        else:
            cursor = self._conn.cursor()
            cursor.execute("SELECT key, value FROM knowledge_vault")
            result = {}
            for key, value in cursor.fetchall():
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            return result

    def forget_fact(self, key: str) -> bool:
        """Remove a fact from the knowledge vault."""
        self._knowledge_cache.pop(key, None)
        if self.db_type == "tinydb":
            Fact = Query()
            removed = self._facts_table.remove(Fact.key == key)
            return len(removed) > 0
        else:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM knowledge_vault WHERE key = ?", (key,))
            self._conn.commit()
            return cursor.rowcount > 0

    # ── Per-Skill Storage ──────────────────────────────────────────────

    def skill_store(self, skill_name: str, key: str, value: Any) -> None:
        """Store data for a specific skill."""
        if skill_name not in self._skill_cache:
            self._skill_cache[skill_name] = {}
        self._skill_cache[skill_name][key] = value
        
        if self.db_type == "tinydb":
            SkillQ = Query()
            self._skills_table.upsert(
                {"skill_name": skill_name, "key": key, "value": value, "timestamp": time.time()},
                (SkillQ.skill_name == skill_name) & (SkillQ.key == key),
            )
        else:
            self._conn.execute(
                "INSERT OR REPLACE INTO skill_data (skill_name, key, value, timestamp) VALUES (?, ?, ?, ?)",
                (skill_name, key, json.dumps(value) if not isinstance(value, str) else value, time.time()),
            )
            self._conn.commit()

    def skill_recall(self, skill_name: str, key: str) -> Optional[Any]:
        """Recall data stored by a specific skill."""
        if skill_name in self._skill_cache and key in self._skill_cache[skill_name]:
            return self._skill_cache[skill_name][key]
            
        result_val = None
        if self.db_type == "tinydb":
            SkillQ = Query()
            result = self._skills_table.search(
                (SkillQ.skill_name == skill_name) & (SkillQ.key == key)
            )
            result_val = result[0]["value"] if result else None
        else:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT value FROM skill_data WHERE skill_name = ? AND key = ?",
                (skill_name, key),
            )
            row = cursor.fetchone()
            if row:
                try:
                    result_val = json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    result_val = row[0]
                    
        if skill_name not in self._skill_cache:
            self._skill_cache[skill_name] = {}
        self._skill_cache[skill_name][key] = result_val
        return result_val

    def skill_get_all(self, skill_name: str) -> dict[str, Any]:
        """Get all data for a specific skill."""
        if self.db_type == "tinydb":
            SkillQ = Query()
            results = self._skills_table.search(SkillQ.skill_name == skill_name)
            return {item["key"]: item["value"] for item in results}
        else:
            cursor = self._conn.cursor()
            cursor.execute("SELECT key, value FROM skill_data WHERE skill_name = ?", (skill_name,))
            result = {}
            for key, value in cursor.fetchall():
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            return result

    # ── Lifecycle ──────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the database connection."""
        if self.db_type == "tinydb":
            self._db.close()
        else:
            self._conn.close()
        logger.info("Memory database closed")

    @property
    def stats(self) -> dict:
        """Return memory usage statistics."""
        if self.db_type == "tinydb":
            return {
                "backend": "tinydb",
                "chat_messages": len(self._chat_table),
                "facts": len(self._facts_table),
                "skill_entries": len(self._skills_table),
                "db_path": str(self._db_path),
            }
        else:
            cursor = self._conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chat_history")
            chat_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM knowledge_vault")
            facts_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM skill_data")
            skill_count = cursor.fetchone()[0]
            return {
                "backend": "sqlite",
                "chat_messages": chat_count,
                "facts": facts_count,
                "skill_entries": skill_count,
                "db_path": str(self._db_path),
            }
