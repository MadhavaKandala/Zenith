"""
Face Authentication — LBPH-based face recognition for Zenith.

Uses OpenCV's Local Binary Patterns Histograms (LBPH) face recognizer
for local-first, privacy-preserving face authentication.

Usage:
    from core.vision.face_auth import FaceAuthenticator
    auth = FaceAuthenticator()
    auth.enroll_user("madhava", ["face1.jpg", "face2.jpg"])
    is_authenticated, confidence = auth.authenticate("test_face.jpg")
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("zenith.vision.face_auth")

try:
    import cv2
    import numpy as np

    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    logger.warning(
        "OpenCV not installed. Face authentication will be unavailable. "
        "Install with: pip install opencv-contrib-python"
    )


class FaceAuthenticator:
    """LBPH face recognizer for local-first authentication."""

    DEFAULT_MODEL_DIR = os.path.join(os.path.expanduser("~"), ".zenith", "face_models")
    CONFIDENCE_THRESHOLD = 80.0  # Lower is better in LBPH; values < threshold pass

    def __init__(
        self,
        model_dir: Optional[str] = None,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ):
        """
        Initialize the face authenticator.

        Args:
            model_dir: Directory to store/load trained face models.
            confidence_threshold: LBPH confidence threshold (lower = stricter).
        """
        self.available = _CV2_AVAILABLE
        self.model_dir = Path(model_dir or self.DEFAULT_MODEL_DIR)
        self.confidence_threshold = confidence_threshold
        self._recognizer = None
        self._face_cascade = None
        self._label_map: dict[int, str] = {}

        if self.available:
            self.model_dir.mkdir(parents=True, exist_ok=True)
            self._recognizer = cv2.face.LBPHFaceRecognizer_create(
                radius=1, neighbors=8, grid_x=8, grid_y=8
            )
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
            self._load_model()

        logger.info(
            "Face authenticator initialized (available=%s, threshold=%.1f)",
            self.available,
            self.confidence_threshold,
        )

    def _detect_faces(self, gray_image) -> list:
        """Detect faces in a grayscale image."""
        if self._face_cascade is None:
            return []
        faces = self._face_cascade.detectMultiScale(
            gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
        )
        return faces if len(faces) > 0 else []

    def _preprocess_image(self, image_path: str | Path):
        """Load and preprocess an image for face recognition."""
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        return gray

    def _model_path(self) -> Path:
        return self.model_dir / "zenith_face_model.yml"

    def _label_map_path(self) -> Path:
        return self.model_dir / "label_map.txt"

    def _save_model(self) -> None:
        """Save the trained model and label map to disk."""
        if self._recognizer is not None:
            self._recognizer.save(str(self._model_path()))

        with open(self._label_map_path(), "w", encoding="utf-8") as f:
            for label_id, name in self._label_map.items():
                f.write(f"{label_id}:{name}\n")

        logger.info("Face model saved to %s", self.model_dir)

    def _load_model(self) -> bool:
        """Load a previously trained model from disk."""
        model_file = self._model_path()
        label_file = self._label_map_path()

        if not model_file.is_file() or not label_file.is_file():
            logger.info("No existing face model found at %s", self.model_dir)
            return False

        try:
            self._recognizer.read(str(model_file))
            self._label_map = {}
            with open(label_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if ":" in line:
                        parts = line.split(":", 1)
                        self._label_map[int(parts[0])] = parts[1]

            logger.info(
                "Face model loaded: %d enrolled user(s)", len(self._label_map)
            )
            return True
        except Exception as exc:
            logger.error("Failed to load face model: %s", exc)
            return False

    def enroll_user(self, user_name: str, image_paths: list[str | Path]) -> bool:
        """
        Enroll a user by training on multiple face images.

        Args:
            user_name: Unique identifier for the user.
            image_paths: List of paths to face images of the user.

        Returns:
            True if enrollment was successful.
        """
        if not self.available:
            raise RuntimeError("OpenCV is not available for face authentication.")

        faces = []
        label_id = max(self._label_map.keys(), default=-1) + 1

        for img_path in image_paths:
            try:
                gray = self._preprocess_image(img_path)
                detected = self._detect_faces(gray)
                for x, y, w, h in detected:
                    face_roi = gray[y : y + h, x : x + w]
                    face_roi = cv2.resize(face_roi, (200, 200))
                    faces.append(face_roi)
            except Exception as exc:
                logger.warning("Skipping image %s: %s", img_path, exc)

        if not faces:
            logger.error("No faces detected in provided images for user '%s'", user_name)
            return False

        labels = [label_id] * len(faces)
        self._label_map[label_id] = user_name

        if len(self._label_map) == 1:
            self._recognizer.train(faces, np.array(labels))
        else:
            self._recognizer.update(faces, np.array(labels))

        self._save_model()
        logger.info(
            "Enrolled user '%s' with %d face samples (label=%d)",
            user_name,
            len(faces),
            label_id,
        )
        return True

    def authenticate(self, image_path: str | Path) -> tuple[bool, float, str]:
        """
        Authenticate a face against enrolled users.

        Args:
            image_path: Path to the face image to authenticate.

        Returns:
            Tuple of (is_authenticated, confidence, user_name).
            confidence is the LBPH distance (lower = better match).
        """
        if not self.available:
            raise RuntimeError("OpenCV is not available for face authentication.")

        if not self._label_map:
            logger.warning("No enrolled users. Authentication will fail.")
            return False, 999.0, "unknown"

        try:
            gray = self._preprocess_image(image_path)
            detected = self._detect_faces(gray)

            if len(detected) == 0:
                logger.warning("No face detected in authentication image")
                return False, 999.0, "no_face"

            # Use the largest detected face
            x, y, w, h = max(detected, key=lambda f: f[2] * f[3])
            face_roi = gray[y : y + h, x : x + w]
            face_roi = cv2.resize(face_roi, (200, 200))

            label_id, confidence = self._recognizer.predict(face_roi)
            user_name = self._label_map.get(label_id, "unknown")
            is_authenticated = confidence < self.confidence_threshold

            logger.info(
                "Authentication result: user=%s, confidence=%.2f, authenticated=%s",
                user_name,
                confidence,
                is_authenticated,
            )
            return is_authenticated, confidence, user_name

        except Exception as exc:
            logger.error("Authentication failed: %s", exc)
            return False, 999.0, "error"

    def authenticate_from_camera(self, camera_index: int = 0) -> tuple[bool, float, str]:
        """
        Capture a frame from the webcam and authenticate.

        Args:
            camera_index: Camera device index (default: 0).

        Returns:
            Tuple of (is_authenticated, confidence, user_name).
        """
        if not self.available:
            raise RuntimeError("OpenCV is not available.")

        cap = cv2.VideoCapture(camera_index)
        try:
            if not cap.isOpened():
                logger.error("Cannot open camera %d", camera_index)
                return False, 999.0, "camera_error"

            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to capture frame from camera")
                return False, 999.0, "capture_error"

            # Save temp frame and authenticate
            temp_path = self.model_dir / "_temp_auth_frame.jpg"
            cv2.imwrite(str(temp_path), frame)
            result = self.authenticate(temp_path)
            temp_path.unlink(missing_ok=True)
            return result
        finally:
            cap.release()

    @property
    def enrolled_users(self) -> list[str]:
        """Return list of enrolled user names."""
        return list(self._label_map.values())

    @property
    def is_model_trained(self) -> bool:
        """Check if a face model has been trained."""
        return len(self._label_map) > 0
