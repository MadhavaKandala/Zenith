"""
Zenith Vision & Recognition Engine
===================================
Provides OCR (via Tesseract), face authentication (LBPH),
and object detection (YOLOv8n) capabilities.
"""

from core.vision.ocr import OCREngine
from core.vision.face_auth import FaceAuthenticator
from core.vision.object_detect import ObjectDetector

__all__ = ["OCREngine", "FaceAuthenticator", "ObjectDetector"]
