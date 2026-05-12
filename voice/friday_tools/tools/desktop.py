"""
Desktop tools — Screenshot capture, application control, and desktop automation
for the MCP server.
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

try:
    from core.desktop.controller import DesktopController
    _DESKTOP_AVAILABLE = True
except ImportError:
    _DESKTOP_AVAILABLE = False

try:
    from core.vision.ocr import OCREngine
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False


def register(mcp):

    @mcp.tool()
    async def take_screenshot() -> str:
        """Take a screenshot of the current screen and save it."""
        if not _DESKTOP_AVAILABLE:
            return "Desktop control is not available. Install pyautogui: pip install pyautogui"

        ctrl = DesktopController()
        try:
            filepath = ctrl.take_screenshot()
            return f"Screenshot saved to {filepath}, sir."
        except Exception as e:
            return f"Failed to take screenshot: {str(e)}"

    @mcp.tool()
    async def open_desktop_app(app_name: str) -> str:
        """Open a desktop application by name.

        Args:
            app_name: Name of the application to open (e.g., 'notepad', 'chrome')
        """
        if not _DESKTOP_AVAILABLE:
            return "Desktop control is not available."

        ctrl = DesktopController()
        success = ctrl.open_application(app_name)
        if success:
            return f"Opened {app_name} for you, sir."
        return f"Failed to open {app_name}, sir."

    @mcp.tool()
    async def read_screen_text() -> str:
        """Read all visible text from the current screen using OCR."""
        if not _OCR_AVAILABLE:
            return "OCR is not available. Install pytesseract and Pillow."

        ocr = OCREngine()
        try:
            text = ocr.screenshot_to_text()
            if text:
                return f"Screen text: {text[:2000]}"
            return "No text detected on screen."
        except Exception as e:
            return f"OCR failed: {str(e)}"

    @mcp.tool()
    async def get_screen_info() -> dict:
        """Get information about the current screen and active window."""
        if not _DESKTOP_AVAILABLE:
            return {"error": "Desktop control not available"}

        ctrl = DesktopController()
        try:
            width, height = ctrl.get_screen_size()
            mouse_x, mouse_y = ctrl.get_mouse_position()
            title = ctrl.get_active_window_title()
            return {
                "screen_size": f"{width}x{height}",
                "mouse_position": f"({mouse_x}, {mouse_y})",
                "active_window": title or "Unknown",
            }
        except Exception as e:
            return {"error": str(e)}
