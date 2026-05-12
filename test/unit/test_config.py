"""
Tests for the Configuration Loader and Validator.
"""

import os
import sys
import tempfile
import unittest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestConfigLoader(unittest.TestCase):
    """Test the YAML config loader."""

    def test_import(self):
        """Config loader should be importable."""
        from config.loader import load_zenith_config
        self.assertIsNotNone(load_zenith_config)

    def test_load_config(self):
        """Should load the zenith.yaml config file."""
        from config.loader import load_zenith_config
        config = load_zenith_config()
        self.assertIsInstance(config, dict)
        self.assertIn('server', config)
        self.assertIn('llm', config)

    def test_env_resolution(self):
        """Should resolve environment variable placeholders."""
        from config.loader import _resolve_env
        os.environ['TEST_KEY_12345'] = 'test_value'
        result = _resolve_env('${TEST_KEY_12345}')
        self.assertEqual(result, 'test_value')
        del os.environ['TEST_KEY_12345']

    def test_nested_resolution(self):
        """Should resolve nested env vars."""
        from config.loader import _resolve_env
        os.environ['NESTED_TEST'] = 'nested'
        data = {'level1': {'level2': '${NESTED_TEST}'}}
        result = _resolve_env(data)
        self.assertEqual(result['level1']['level2'], 'nested')
        del os.environ['NESTED_TEST']


class TestConfigValidator(unittest.TestCase):
    """Test the config schema validator."""

    def test_import(self):
        """Validator should be importable."""
        from config.validator import validate_config
        self.assertIsNotNone(validate_config)

    def test_valid_config(self):
        """Should pass for a complete valid config."""
        from config.validator import validate_config
        config = {
            'server': {'port': 1337},
            'voice': {'stt_provider': 'groq_whisper', 'language': 'en-US'},
            'llm': {'primary': 'gemini', 'gemini': {'api_key': 'test'}},
            'personality': {'name': 'Zenith', 'style': 'friday'},
            'skills': {'enabled': True},
            'memory': {'db_type': 'tinydb'},
            'ui': {'theme': 'stark'},
        }
        errors = validate_config(config)
        self.assertEqual(len(errors), 0)

    def test_missing_required_section(self):
        """Should detect missing required sections."""
        from config.validator import validate_config
        config = {'server': {'port': 1337}}
        errors = validate_config(config)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('voice' in e for e in errors))

    def test_missing_required_key(self):
        """Should detect missing required keys."""
        from config.validator import validate_config
        config = {
            'server': {},  # missing 'port'
            'voice': {'stt_provider': 'groq', 'language': 'en'},
            'llm': {'primary': 'gemini', 'gemini': {}},
            'personality': {'name': 'Z', 'style': 'friday'},
            'skills': {'enabled': True},
            'memory': {'db_type': 'tinydb'},
            'ui': {'theme': 'stark'},
        }
        errors = validate_config(config)
        self.assertTrue(any('server.port' in e for e in errors))

    def test_invalid_type(self):
        """Should detect invalid types."""
        from config.validator import validate_config
        config = {
            'server': {'port': 'not_a_number'},
            'voice': {'stt_provider': 'groq', 'language': 'en'},
            'llm': {'primary': 'gemini', 'gemini': {}},
            'personality': {'name': 'Z', 'style': 'friday'},
            'skills': {'enabled': True},
            'memory': {'db_type': 'tinydb'},
            'ui': {'theme': 'stark'},
        }
        errors = validate_config(config)
        self.assertTrue(any('type' in e.lower() for e in errors))

    def test_unconfigured_fallback_provider(self):
        """Should warn about fallback providers without config."""
        from config.validator import validate_config
        config = {
            'server': {'port': 1337},
            'voice': {'stt_provider': 'groq', 'language': 'en'},
            'llm': {'primary': 'gemini', 'gemini': {}, 'fallback': ['groq']},
            'personality': {'name': 'Z', 'style': 'friday'},
            'skills': {'enabled': True},
            'memory': {'db_type': 'tinydb'},
            'ui': {'theme': 'stark'},
        }
        errors = validate_config(config)
        self.assertTrue(any('groq' in e for e in errors))

    def test_non_dict_input(self):
        """Should handle non-dict input."""
        from config.validator import validate_config
        errors = validate_config("not a dict")
        self.assertTrue(any('dictionary' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
