"""
Zenith Core Module
==================
Central package exposing all core subsystems:
  - Vision & Recognition (OCR, Face Auth, Object Detection)
  - Desktop Automation (PyAutoGUI)
  - Browser Automation (Playwright)
  - Global Memory (TinyDB/SQLite)
"""

from core.vision import OCREngine, FaceAuthenticator, ObjectDetector
from core.desktop import DesktopController
from core.browser import BrowserAutomation
from core.memory import ZenithMemory

__all__ = [
    "OCREngine",
    "FaceAuthenticator",
    "ObjectDetector",
    "DesktopController",
    "BrowserAutomation",
    "ZenithMemory",
]
