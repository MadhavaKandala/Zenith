"""
Object Detection — YOLOv8n-based object detection for Zenith.

Uses Ultralytics YOLOv8 nano model for efficient real-time object detection
in screenshots and camera feeds.

Usage:
    from core.vision.object_detect import ObjectDetector
    detector = ObjectDetector()
    results = detector.detect("screenshot.png")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("zenith.vision.object_detect")

try:
    from ultralytics import YOLO

    _YOLO_AVAILABLE = True
except ImportError:
    _YOLO_AVAILABLE = False
    logger.warning(
        "Ultralytics YOLO not installed. Object detection will be unavailable. "
        "Install with: pip install ultralytics"
    )


class DetectionResult:
    """Represents a single object detection result."""

    def __init__(self, label: str, confidence: float, bbox: tuple[int, int, int, int]):
        self.label = label
        self.confidence = confidence
        self.bbox = bbox  # (x1, y1, x2, y2)

    def __repr__(self) -> str:
        return f"DetectionResult(label='{self.label}', conf={self.confidence:.2f}, bbox={self.bbox})"

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "bbox": {"x1": self.bbox[0], "y1": self.bbox[1], "x2": self.bbox[2], "y2": self.bbox[3]},
        }


class ObjectDetector:
    """YOLOv8n object detector for Zenith desktop assistant."""

    DEFAULT_MODEL = "yolov8n.pt"
    DEFAULT_CONFIDENCE = 0.5

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE,
    ):
        """
        Initialize the object detector.

        Args:
            model_path: Path to the YOLO model (auto-downloads yolov8n.pt if None).
            confidence_threshold: Minimum confidence for detections (0.0–1.0).
        """
        self.available = _YOLO_AVAILABLE
        self.confidence_threshold = confidence_threshold
        self._model = None

        if self.available:
            try:
                self._model = YOLO(model_path or self.DEFAULT_MODEL)
                logger.info("YOLOv8 model loaded: %s", model_path or self.DEFAULT_MODEL)
            except Exception as exc:
                logger.error("Failed to load YOLO model: %s", exc)
                self.available = False

    def detect(self, image_path: str | Path) -> list[DetectionResult]:
        """
        Run object detection on an image file.

        Args:
            image_path: Path to the image file.

        Returns:
            List of DetectionResult objects.
        """
        if not self.available or self._model is None:
            raise RuntimeError("YOLO model is not available.")

        image_path = Path(image_path)
        if not image_path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        results = self._model(str(image_path), conf=self.confidence_threshold, verbose=False)
        detections = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0])
                label = result.names.get(cls_id, f"class_{cls_id}")
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    DetectionResult(
                        label=label,
                        confidence=confidence,
                        bbox=(int(x1), int(y1), int(x2), int(y2)),
                    )
                )

        logger.info(
            "Detected %d objects in %s", len(detections), image_path.name
        )
        return detections

    def detect_from_screenshot(self) -> list[DetectionResult]:
        """
        Capture the current screen and run object detection.

        Returns:
            List of DetectionResult objects.
        """
        if not self.available:
            raise RuntimeError("YOLO model is not available.")

        try:
            import pyautogui
            import tempfile
            import os

            screenshot = pyautogui.screenshot()
            temp_path = os.path.join(tempfile.gettempdir(), "_zenith_detect.png")
            screenshot.save(temp_path)
            results = self.detect(temp_path)
            os.unlink(temp_path)
            return results
        except ImportError:
            logger.error("pyautogui not installed for screen capture")
            return []

    def describe_scene(self, image_path: str | Path) -> str:
        """
        Generate a natural-language description of detected objects.

        Args:
            image_path: Path to the image.

        Returns:
            Human-readable description string.
        """
        detections = self.detect(image_path)
        if not detections:
            return "No objects detected in the image."

        # Group by label
        counts: dict[str, int] = {}
        for det in detections:
            counts[det.label] = counts.get(det.label, 0) + 1

        parts = []
        for label, count in sorted(counts.items(), key=lambda x: -x[1]):
            if count == 1:
                parts.append(f"a {label}")
            else:
                parts.append(f"{count} {label}s")

        return "I can see " + ", ".join(parts) + " in the image."
