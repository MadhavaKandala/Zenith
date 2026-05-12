"""
Tests for the Vision & Recognition Engine.
Tests OCR, face authentication, and object detection modules.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestOCREngine(unittest.TestCase):
    """Test cases for the Tesseract OCR engine."""

    def test_import(self):
        """OCR module should be importable."""
        from core.vision.ocr import OCREngine
        self.assertIsNotNone(OCREngine)

    def test_instantiation(self):
        """OCR engine should instantiate without errors."""
        from core.vision.ocr import OCREngine
        engine = OCREngine()
        self.assertIsNotNone(engine)
        self.assertIsInstance(engine.lang, str)
        self.assertEqual(engine.lang, 'eng')

    def test_custom_language(self):
        """OCR engine should accept custom language codes."""
        from core.vision.ocr import OCREngine
        engine = OCREngine(lang='fra')
        self.assertEqual(engine.lang, 'fra')

    def test_file_not_found(self):
        """extract_text should raise FileNotFoundError for missing files."""
        from core.vision.ocr import OCREngine
        engine = OCREngine()
        if engine.available:
            with self.assertRaises(FileNotFoundError):
                engine.extract_text('/nonexistent/path.png')


class TestFaceAuthenticator(unittest.TestCase):
    """Test cases for the LBPH face authenticator."""

    def test_import(self):
        """Face auth module should be importable."""
        from core.vision.face_auth import FaceAuthenticator
        self.assertIsNotNone(FaceAuthenticator)

    def test_instantiation(self):
        """Face authenticator should instantiate without errors."""
        from core.vision.face_auth import FaceAuthenticator
        auth = FaceAuthenticator()
        self.assertIsNotNone(auth)
        self.assertIsInstance(auth.confidence_threshold, float)

    def test_no_enrolled_users(self):
        """Should return empty list when no users enrolled."""
        from core.vision.face_auth import FaceAuthenticator
        auth = FaceAuthenticator(model_dir=os.path.join(os.path.dirname(__file__), '_test_faces'))
        self.assertEqual(auth.enrolled_users, [])

    def test_model_not_trained(self):
        """is_model_trained should return False initially."""
        from core.vision.face_auth import FaceAuthenticator
        auth = FaceAuthenticator(model_dir=os.path.join(os.path.dirname(__file__), '_test_faces'))
        self.assertFalse(auth.is_model_trained)


class TestObjectDetector(unittest.TestCase):
    """Test cases for the YOLOv8n object detector."""

    def test_import(self):
        """Object detection module should be importable."""
        from core.vision.object_detect import ObjectDetector
        self.assertIsNotNone(ObjectDetector)

    def test_instantiation(self):
        """Object detector should instantiate (may fail without YOLO installed)."""
        from core.vision.object_detect import ObjectDetector
        detector = ObjectDetector()
        self.assertIsNotNone(detector)
        self.assertIsInstance(detector.confidence_threshold, float)

    def test_detection_result_class(self):
        """DetectionResult should serialize to dict correctly."""
        from core.vision.object_detect import DetectionResult
        result = DetectionResult(label='person', confidence=0.95, bbox=(10, 20, 100, 200))
        d = result.to_dict()
        self.assertEqual(d['label'], 'person')
        self.assertAlmostEqual(d['confidence'], 0.95, places=2)
        self.assertEqual(d['bbox']['x1'], 10)


class TestVisionPackage(unittest.TestCase):
    """Test the vision package init."""

    def test_package_imports(self):
        """Vision package should expose all engines."""
        from core.vision import OCREngine, FaceAuthenticator, ObjectDetector
        self.assertIsNotNone(OCREngine)
        self.assertIsNotNone(FaceAuthenticator)
        self.assertIsNotNone(ObjectDetector)


if __name__ == '__main__':
    unittest.main()
