"""
OCR Engine — Tesseract-based optical character recognition.

Provides text extraction from images and screenshots for the Zenith
desktop assistant.  Falls back gracefully when Tesseract is not installed.

Usage:
    from core.vision.ocr import OCREngine
    engine = OCREngine()
    text = engine.extract_text("screenshot.png")
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("zenith.vision.ocr")

try:
    import pytesseract
    from PIL import Image

    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False
    logger.warning(
        "pytesseract or Pillow not installed. OCR features will be unavailable. "
        "Install with: pip install pytesseract Pillow"
    )


class OCREngine:
    """Tesseract OCR wrapper for Zenith."""

    def __init__(self, tesseract_cmd: Optional[str] = None, lang: str = "eng"):
        """
        Initialize the OCR engine.

        Args:
            tesseract_cmd: Path to the tesseract binary. Auto-detected if None.
            lang: Tesseract language code (default: 'eng').
        """
        self.lang = lang
        self.available = _TESSERACT_AVAILABLE

        if self.available and tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif self.available:
            # Try common Windows paths
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            env_path = os.getenv("TESSERACT_CMD")
            if env_path:
                common_paths.insert(0, env_path)

            for path in common_paths:
                if os.path.isfile(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break

        logger.info("OCR engine initialized (available=%s, lang=%s)", self.available, lang)

    def extract_text(self, image_path: str | Path) -> str:
        """
        Extract text from an image file using Tesseract OCR.

        Args:
            image_path: Path to the image file (PNG, JPEG, BMP, TIFF).

        Returns:
            Extracted text as a string. Empty string on failure.

        Raises:
            FileNotFoundError: If the image file does not exist.
            RuntimeError: If Tesseract is not available.
        """
        if not self.available:
            raise RuntimeError(
                "Tesseract OCR is not available. "
                "Install pytesseract and Pillow: pip install pytesseract Pillow"
            )

        image_path = Path(image_path)
        if not image_path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=self.lang)
            logger.info(
                "OCR extracted %d characters from %s", len(text.strip()), image_path.name
            )
            return text.strip()
        except Exception as exc:
            logger.error("OCR extraction failed for %s: %s", image_path, exc)
            return ""

    def extract_text_from_image(self, pil_image) -> str:
        """
        Extract text directly from a PIL Image object.

        Args:
            pil_image: A PIL.Image.Image instance.

        Returns:
            Extracted text string.
        """
        if not self.available:
            raise RuntimeError("Tesseract OCR is not available.")

        try:
            text = pytesseract.image_to_string(pil_image, lang=self.lang)
            return text.strip()
        except Exception as exc:
            logger.error("OCR extraction from PIL image failed: %s", exc)
            return ""

    def extract_data(self, image_path: str | Path) -> dict:
        """
        Extract structured OCR data with bounding boxes and confidence scores.

        Args:
            image_path: Path to the image file.

        Returns:
            Dictionary with keys: text, conf, left, top, width, height.
        """
        if not self.available:
            raise RuntimeError("Tesseract OCR is not available.")

        image_path = Path(image_path)
        if not image_path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            img = Image.open(image_path)
            data = pytesseract.image_to_data(img, lang=self.lang, output_type=pytesseract.Output.DICT)
            logger.info("OCR data extracted with %d entries from %s", len(data.get("text", [])), image_path.name)
            return data
        except Exception as exc:
            logger.error("OCR data extraction failed: %s", exc)
            return {}

    def screenshot_to_text(self) -> str:
        """
        Capture the current screen and extract text via OCR.

        Returns:
            Extracted text from the current screen.
        """
        if not self.available:
            raise RuntimeError("Tesseract OCR is not available.")

        try:
            import pyautogui

            screenshot = pyautogui.screenshot()
            return self.extract_text_from_image(screenshot)
        except ImportError:
            logger.error("pyautogui not installed for screen capture")
            return ""
        except Exception as exc:
            logger.error("Screenshot OCR failed: %s", exc)
            return ""
