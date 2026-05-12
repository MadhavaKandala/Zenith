"""
Tests for the Global Memory Abstraction Layer.
Tests both TinyDB and SQLite backends.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestZenithMemoryTinyDB(unittest.TestCase):
    """Test ZenithMemory with TinyDB backend."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_memory.json')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_memory(self):
        from core.memory import ZenithMemory
        return ZenithMemory(db_type='tinydb', db_path=self.db_path)

    def test_instantiation(self):
        """Memory should instantiate with TinyDB."""
        mem = self._get_memory()
        self.assertIsNotNone(mem)
        mem.close()

    def test_store_and_recall_fact(self):
        """Should store and recall facts."""
        mem = self._get_memory()
        mem.store_fact('user_name', 'Madhava')
        result = mem.recall_fact('user_name')
        self.assertEqual(result, 'Madhava')
        mem.close()

    def test_store_chat_message(self):
        """Should store chat messages."""
        mem = self._get_memory()
        mem.store_chat('user', 'Hello Zenith')
        mem.store_chat('assistant', 'Hello sir, how can I help?')
        history = mem.get_chat_history()
        self.assertEqual(len(history), 2)
        mem.close()

    def test_chat_history_limit(self):
        """Should enforce chat history limit."""
        mem = self._get_memory()
        mem.chat_history_limit = 5
        for i in range(10):
            mem.store_chat('user', f'Message {i}')
        history = mem.get_chat_history(limit=100)
        self.assertLessEqual(len(history), 6)  # Allow small buffer
        mem.close()

    def test_forget_fact(self):
        """Should remove facts."""
        mem = self._get_memory()
        mem.store_fact('temp_key', 'temp_value')
        self.assertEqual(mem.recall_fact('temp_key'), 'temp_value')
        removed = mem.forget_fact('temp_key')
        self.assertTrue(removed)
        self.assertIsNone(mem.recall_fact('temp_key'))
        mem.close()

    def test_skill_storage(self):
        """Should store and recall per-skill data."""
        mem = self._get_memory()
        mem.skill_store('todo_list', 'items', ['buy milk', 'walk dog'])
        result = mem.skill_recall('todo_list', 'items')
        self.assertEqual(result, ['buy milk', 'walk dog'])
        mem.close()

    def test_get_all_facts(self):
        """Should return all stored facts."""
        mem = self._get_memory()
        mem.store_fact('key1', 'value1')
        mem.store_fact('key2', 'value2')
        facts = mem.get_all_facts()
        self.assertEqual(facts['key1'], 'value1')
        self.assertEqual(facts['key2'], 'value2')
        mem.close()

    def test_clear_chat_history(self):
        """Should clear all chat history."""
        mem = self._get_memory()
        mem.store_chat('user', 'test message')
        mem.clear_chat_history()
        history = mem.get_chat_history()
        self.assertEqual(len(history), 0)
        mem.close()

    def test_stats(self):
        """Should return memory statistics."""
        mem = self._get_memory()
        mem.store_chat('user', 'test')
        mem.store_fact('key', 'value')
        stats = mem.stats
        self.assertEqual(stats['backend'], 'tinydb')
        self.assertGreaterEqual(stats['chat_messages'], 1)
        self.assertGreaterEqual(stats['facts'], 1)
        mem.close()


class TestZenithMemorySQLite(unittest.TestCase):
    """Test ZenithMemory with SQLite backend."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_memory.db')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_memory(self):
        from core.memory import ZenithMemory
        return ZenithMemory(db_type='sqlite', db_path=self.db_path)

    def test_instantiation(self):
        """Memory should instantiate with SQLite."""
        mem = self._get_memory()
        self.assertIsNotNone(mem)
        mem.close()

    def test_store_and_recall_fact(self):
        """Should store and recall facts with SQLite."""
        mem = self._get_memory()
        mem.store_fact('favorite_color', 'blue')
        result = mem.recall_fact('favorite_color')
        self.assertEqual(result, 'blue')
        mem.close()

    def test_chat_roundtrip(self):
        """Should store and retrieve chat with SQLite."""
        mem = self._get_memory()
        mem.store_chat('user', 'What time is it?')
        mem.store_chat('assistant', 'It is 2:30 PM IST, sir.')
        history = mem.get_chat_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['role'], 'assistant')  # Most recent first
        mem.close()

    def test_stats_sqlite(self):
        """Should return SQLite stats."""
        mem = self._get_memory()
        stats = mem.stats
        self.assertEqual(stats['backend'], 'sqlite')
        mem.close()


class TestZenithMemoryInvalidBackend(unittest.TestCase):
    """Test error handling for invalid backends."""

    def test_invalid_backend_raises(self):
        """Should raise ValueError for unknown db_type."""
        from core.memory import ZenithMemory
        with self.assertRaises(ValueError):
            ZenithMemory(db_type='mongodb')


if __name__ == '__main__':
    unittest.main()
