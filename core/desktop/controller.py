"""
Desktop Control — PyAutoGUI-based desktop automation for Zenith.

Provides mouse, keyboard, and screen control capabilities for the desktop
assistant. Includes safety guards to prevent runaway automation.

Usage:
    from core.desktop.controller import DesktopController
    ctrl = DesktopController()
    ctrl.click(100, 200)
    ctrl.type_text("Hello, sir.")
    ctrl.take_screenshot("capture.png")
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("zenith.desktop.controller")

try:
    import pyautogui

    _PYAUTOGUI_AVAILABLE = True
except ImportError:
    _PYAUTOGUI_AVAILABLE = False
    logger.warning(
        "PyAutoGUI not installed. Desktop control will be unavailable. "
        "Install with: pip install pyautogui"
    )


class DesktopController:
    """Desktop automation controller using PyAutoGUI."""

    SCREENSHOTS_DIR = os.path.join(os.path.expanduser("~"), ".zenith", "screenshots")

    def __init__(self, safety_enabled: bool = True):
        """
        Initialize the desktop controller.

        Args:
            safety_enabled: Whether to enable PyAutoGUI failsafe (default True).
        """
        self.available = _PYAUTOGUI_AVAILABLE
        self.safety_enabled = safety_enabled

        if self.available:
            self._old_failsafe = getattr(pyautogui, "FAILSAFE", True)
            self._old_pause = getattr(pyautogui, "PAUSE", 0.1)
            pyautogui.FAILSAFE = safety_enabled
            pyautogui.PAUSE = 0.1
            Path(self.SCREENSHOTS_DIR).mkdir(parents=True, exist_ok=True)

    def __del__(self):
        if getattr(self, "available", False):
            pyautogui.FAILSAFE = getattr(self, "_old_failsafe", True)
            pyautogui.PAUSE = getattr(self, "_old_pause", 0.1)

        logger.info(
            "Desktop controller initialized (available=%s, safety=%s)",
            self.available,
            safety_enabled,
        )

    def _require_available(self) -> None:
        if not self.available:
            raise RuntimeError(
                "PyAutoGUI is not available. Install with: pip install pyautogui"
            )

    # ── Mouse Control ──────────────────────────────────────────────────

    def click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> None:
        """
        Click at screen coordinates.

        Args:
            x: X coordinate.
            y: Y coordinate.
            button: 'left', 'right', or 'middle'.
            clicks: Number of clicks (2 for double-click).
        """
        self._require_available()
        pyautogui.click(x=x, y=y, button=button, clicks=clicks)
        logger.info("Clicked (%d, %d) button=%s clicks=%d", x, y, button, clicks)

    def move_to(self, x: int, y: int, duration: float = 0.3) -> None:
        """Move mouse to coordinates with smooth animation."""
        self._require_available()
        pyautogui.moveTo(x, y, duration=duration)

    def drag_to(self, x: int, y: int, duration: float = 0.5, button: str = "left") -> None:
        """Drag from current position to target coordinates."""
        self._require_available()
        pyautogui.dragTo(x, y, duration=duration, button=button)
        logger.info("Dragged to (%d, %d)", x, y)

    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Scroll the mouse wheel. Positive = up, negative = down."""
        self._require_available()
        pyautogui.scroll(clicks, x=x, y=y)

    def get_mouse_position(self) -> tuple[int, int]:
        """Return current mouse (x, y) position."""
        self._require_available()
        pos = pyautogui.position()
        return pos.x, pos.y

    # ── Keyboard Control ───────────────────────────────────────────────

    def type_text(self, text: str, interval: float = 0.02) -> None:
        """
        Type text character by character.

        Args:
            text: The text string to type.
            interval: Delay between keystrokes in seconds.
        """
        self._require_available()
        pyautogui.typewrite(text, interval=interval)
        logger.info("Typed %d characters", len(text))

    def hotkey(self, *keys: str) -> None:
        """
        Press a keyboard shortcut (e.g., ctrl+c).

        Args:
            *keys: Key names like 'ctrl', 'alt', 'shift', 'c', etc.
        """
        self._require_available()
        pyautogui.hotkey(*keys)
        logger.info("Hotkey pressed: %s", "+".join(keys))

    def press(self, key: str, presses: int = 1) -> None:
        """Press a single key."""
        self._require_available()
        pyautogui.press(key, presses=presses)

    # ── Screen Control ─────────────────────────────────────────────────

    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """
        Take a screenshot and save it to disk.

        Args:
            filename: Output filename (auto-generated timestamp if None).

        Returns:
            Absolute path to the saved screenshot.
        """
        self._require_available()
        if filename is None:
            filename = f"zenith_screenshot_{int(time.time())}.png"

        filepath = os.path.join(self.SCREENSHOTS_DIR, filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        logger.info("Screenshot saved: %s", filepath)
        return filepath

    def get_screen_size(self) -> tuple[int, int]:
        """Return the screen resolution as (width, height)."""
        self._require_available()
        size = pyautogui.size()
        return size.width, size.height

    def locate_on_screen(self, image_path: str, confidence: float = 0.8) -> Optional[tuple[int, int]]:
        """
        Find an image on screen and return its center coordinates.

        Args:
            image_path: Path to the template image to find.
            confidence: Match confidence threshold (0.0–1.0).

        Returns:
            (x, y) center coordinates, or None if not found.
        """
        self._require_available()
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if location:
                logger.info("Found image at (%d, %d)", location.x, location.y)
                return location.x, location.y
            return None
        except Exception as exc:
            if "opencv" in str(exc).lower() or isinstance(exc, ImportError):
                logger.error("opencv-python is required for confidence-based matching. Install with: pip install opencv-python")
            else:
                logger.error("Image locate failed: %s", exc)
            return None

    # ── Window Management ──────────────────────────────────────────────

    def get_active_window_title(self) -> str:
        """Return the title of the currently active window."""
        self._require_available()
        try:
            win = pyautogui.getActiveWindow()
            return win.title if win else ""
        except Exception:
            return ""

    # ── Compound Actions ───────────────────────────────────────────────

    def open_application(self, name: str) -> bool:
        """
        Open an application by name using OS-native methods.

        Args:
            name: Application name (e.g., 'notepad', 'calc', 'chrome').

        Returns:
            True if the application was launched successfully.
        """
        self._require_available()
        import subprocess
        import sys

        try:
            if sys.platform == "win32":
                os.startfile(name)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", name])
            else:
                import shutil
                if shutil.which(name):
                    subprocess.Popen([name])
                else:
                    logger.error("Application %s not found on PATH", name)
                    return False

            logger.info("Opened application: %s", name)
            return True
        except Exception as exc:
            logger.error("Failed to open %s: %s", name, exc)
            return False

    @property
    def _modifier(self) -> str:
        import sys
        return "command" if sys.platform == "darwin" else "ctrl"

    def copy_to_clipboard(self) -> None:
        """Copy the current selection to clipboard (Ctrl+C)."""
        self.hotkey(self._modifier, "c")

    def paste_from_clipboard(self) -> None:
        """Paste from clipboard (Ctrl+V)."""
        self.hotkey(self._modifier, "v")

    def select_all(self) -> None:
        """Select all content (Ctrl+A)."""
        self.hotkey(self._modifier, "a")

    def undo(self) -> None:
        """Undo last action (Ctrl+Z)."""
        self.hotkey(self._modifier, "z")

    def save(self) -> None:
        """Save current document (Ctrl+S)."""
        self.hotkey(self._modifier, "s")
