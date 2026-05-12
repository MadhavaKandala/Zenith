import sys
import os
from unittest.mock import patch, MagicMock, mock_open

# Add python bridge src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../bridges/python/src')))

# Mock sys.argv and open so that utils.py can be imported without crashing
with patch("sys.argv", ["main.py", "dummy.json"]), patch("builtins.open", mock_open(read_data='{"version": "1.0.0"}')):
    from main import main


@patch("main.utils")
@patch("main.import_module")
def test_skill_routing(mock_import, mock_utils):
    mock_utils.get_intent_obj.return_value = {
        'domain': 'system',
        'skill': 'desktop_control',
        'action': 'take_screenshot',
        'lang': 'en',
        'utterance': 'screenshot',
        'current_entities': [],
        'entities': [],
        'current_resolvers': [],
        'resolvers': [],
        'slots': {}
    }
    
    mock_skill = MagicMock()
    mock_import.return_value = mock_skill
    mock_skill.take_screenshot.return_value = '{"key": "screenshot_taken"}'
    
    result = main()
    
    mock_import.assert_called_with('skills.system.desktop_control.src.actions.take_screenshot')
    mock_skill.take_screenshot.assert_called_once()
    assert result == '{"key": "screenshot_taken"}'

@patch("main.utils")
@patch("main.import_module")
def test_skill_routing_error(mock_import, mock_utils):
    mock_utils.get_intent_obj.return_value = {
        'domain': 'system',
        'skill': 'desktop_control',
        'action': 'take_screenshot',
        'lang': 'en',
        'utterance': 'screenshot',
        'current_entities': [],
        'entities': [],
        'current_resolvers': [],
        'resolvers': [],
        'slots': {}
    }
    
    mock_import.side_effect = ModuleNotFoundError("No module named 'skills.system.desktop_control'")
    
    try:
        main()
        assert False, "Should raise ModuleNotFoundError"
    except ModuleNotFoundError:
        pass
