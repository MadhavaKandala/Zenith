#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Desktop Control Skill — Automate desktop actions via PyAutoGUI.

Actions:
  - take_screenshot: Capture the current screen
  - open_app: Open an application by name
  - type_text: Type text using keyboard simulation
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from core.desktop.controller import DesktopController

_ctrl = None


def _get_controller():
    """Lazy-initialize the desktop controller singleton."""
    global _ctrl
    if _ctrl is None:
        _ctrl = DesktopController()
    return _ctrl


def _print_json(key, speech, **kwargs):
    data = {"speech": speech}
    data.update(kwargs)
    print(json.dumps({"key": key, "data": data}))


def take_screenshot(params):
    """Capture the current screen and save it."""
    ctrl = _get_controller()

    try:
        filename = params.get('filename')
        if filename:
            filename = os.path.basename(filename)
        filepath = ctrl.take_screenshot(filename=filename)
        return _print_json("screenshot_taken", "Screenshot captured and saved, sir.", filepath=filepath)
    except RuntimeError as e:
        return _print_json("unavailable", f"Desktop control is not available: {str(e)}")
    except Exception as e:
        return _print_json("error", f"Failed to take screenshot, sir: {str(e)}")


def open_app(params):
    """Open an application by name."""
    ctrl = _get_controller()

    # Extract application name from entities or utterance
    entities = params.get('entities', [])
    app_name = None

    for entity in entities:
        if entity.get('entity') == 'application':
            app_name = entity.get('sourceText', entity.get('resolution', {}).get('value'))
            break

    if not app_name:
        utterance = params.get('utterance', '')
        # Try to extract app name from common patterns
        import re
        match = re.search(r'(?:open|launch|start)\s+(.+)', utterance, re.IGNORECASE)
        if match:
            app_name = match.group(1).strip()

    if not app_name:
        return _print_json("no_app", "Which application would you like me to open, sir?")

    try:
        success = ctrl.open_application(app_name)
        if success:
            return _print_json("app_opened", f"Opening {app_name} for you, sir.")
        else:
            return _print_json("app_failed", f"I was unable to open {app_name}, sir.")
    except RuntimeError as e:
        return _print_json("unavailable", f"Desktop control is not available: {str(e)}")


def type_text(params):
    """Type text using keyboard simulation."""
    ctrl = _get_controller()

    utterance = params.get('utterance', '')
    # Extract the text to type from the utterance
    import re
    match = re.search(r'(?:type|write|input)\s+(.+)', utterance, re.IGNORECASE)
    text_to_type = match.group(1).strip() if match else utterance

    if not text_to_type:
        return _print_json("no_text", "What would you like me to type, sir?")

    try:
        ctrl.type_text(text_to_type)
        return _print_json("text_typed", "Done typing, sir.")
    except RuntimeError as e:
        return _print_json("unavailable", f"Desktop control is not available: {str(e)}")
