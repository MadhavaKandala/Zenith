import sys
import os
import asyncio
from unittest.mock import AsyncMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from providers.manager import ZenithProviderManager

def test_manager_init():
    config = {
        "llm": {
            "gemini": {"api_key": "test_gemini"},
            "groq": {"api_key": "test_groq"}
        }
    }
    manager = ZenithProviderManager(config)
    assert len(manager.providers) == 2
    assert manager.providers[0].name == "gemini"
    assert manager.providers[1].name == "groq"

def test_provider_fallback():
    config = {
        "llm": {
            "gemini": {"api_key": "test_gemini"},
            "groq": {"api_key": "test_groq"}
        }
    }
    manager = ZenithProviderManager(config)
    
    # Mock the first provider to raise an exception
    manager.providers[0].chat = AsyncMock(side_effect=Exception("API Error"))
    # Mock the second provider to succeed
    manager.providers[1].chat = AsyncMock(return_value="Groq response")
    
    result = asyncio.run(manager.chat([{"role": "user", "content": "hello"}]))
    
    assert result == "Groq response"
    assert manager.active_provider == "groq"
    manager.providers[0].chat.assert_called_once()
    manager.providers[1].chat.assert_called_once()

def test_all_providers_fail():
    config = {
        "llm": {
            "gemini": {"api_key": "test_gemini"},
            "groq": {"api_key": "test_groq"}
        }
    }
    manager = ZenithProviderManager(config)
    
    manager.providers[0].chat = AsyncMock(side_effect=Exception("API Error 1"))
    manager.providers[1].chat = AsyncMock(side_effect=Exception("API Error 2"))
    
    try:
        asyncio.run(manager.chat([{"role": "user", "content": "hello"}]))
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "All providers failed" in str(e)
        assert "API Error 1" in str(e)
        assert "API Error 2" in str(e)
