import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from core.memory.memory import ZenithMemory

@pytest.fixture(params=["tinydb", "sqlite"])
def memory_db(request):
    db_type = request.param
    with tempfile.TemporaryDirectory() as tmpdir:
        ext = ".json" if db_type == "tinydb" else ".db"
        db_path = os.path.join(tmpdir, f"test_memory{ext}")
        mem = ZenithMemory(db_type=db_type, db_path=db_path, chat_history_limit=5)
        yield mem
        mem.close()

def test_chat_history(memory_db):
    memory_db.store_chat("user", "Hello")
    memory_db.store_chat("assistant", "Hi there")
    
    history = memory_db.get_chat_history()
    assert len(history) == 2
    assert history[0]["role"] == "assistant"
    assert history[0]["content"] == "Hi there"
    assert history[1]["role"] == "user"
    assert history[1]["content"] == "Hello"

def test_chat_limit(memory_db):
    for i in range(10):
        memory_db.store_chat("user", f"Msg {i}")
        
    history = memory_db.get_chat_history()
    assert len(history) == 5
    # The most recent 5 should be 9, 8, 7, 6, 5
    assert history[0]["content"] == "Msg 9"
    assert history[-1]["content"] == "Msg 5"

def test_knowledge_vault(memory_db):
    memory_db.store_fact("name", "Zenith")
    assert memory_db.recall_fact("name") == "Zenith"
    
    # Test update
    memory_db.store_fact("name", "Zenith AI")
    assert memory_db.recall_fact("name") == "Zenith AI"
    
    # Test forget
    assert memory_db.forget_fact("name") is True
    assert memory_db.recall_fact("name") is None

def test_skill_storage(memory_db):
    memory_db.skill_store("weather", "last_city", "London")
    assert memory_db.skill_recall("weather", "last_city") == "London"
    
    # Test isolation
    memory_db.skill_store("news", "last_city", "Paris")
    assert memory_db.skill_recall("weather", "last_city") == "London"
    assert memory_db.skill_recall("news", "last_city") == "Paris"
    
    # Test get all
    memory_db.skill_store("weather", "unit", "celsius")
    all_weather = memory_db.skill_get_all("weather")
    assert all_weather["last_city"] == "London"
    assert all_weather["unit"] == "celsius"
    assert "last_city" not in memory_db.skill_get_all("unknown")
