from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


class FaceRecognitionService:
    """Modular face-recognition service wrapper.

    The legacy prototype uses Haar Cascade + KNN on pickled sample data. The
    browser-based production system will send captures to this service, which can
    later be upgraded to embedding-based recognition without changing the API
    surface around the application.
    """

    def __init__(self, cascade_path: str | Path | None = None):
        cascade_file = cascade_path or Path(__file__).resolve().parents[3] / "data" / "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(str(cascade_file))
        if self.face_cascade.empty():
            raise FileNotFoundError(f"Could not load Haar cascade file: {cascade_file}")

    def detect_faces(self, image: np.ndarray) -> list[tuple[int, int, int, int]]:
        if image is None or image.size == 0 or image.ndim != 3 or image.shape[2] != 3:
            return []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(60, 60),
        )
        return [tuple(int(value) for value in face) for face in faces]

    def validate_capture(self, image: np.ndarray, face_box: tuple[int, int, int, int]) -> bool:
        if image is None or image.size == 0 or not face_box:
            return False
        x, y, w, h = face_box
        if w < 80 or h < 80:
            return False
        face = image[y : y + h, x : x + w]
        if face.size == 0:
            return False
        gray_face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        brightness = float(gray_face.mean())
        sharpness = float(cv2.Laplacian(gray_face, cv2.CV_64F).var())
        return 35 <= brightness <= 225 and sharpness >= 8

    def recognize(self, image: np.ndarray) -> dict[str, object]:
        faces = self.detect_faces(image)
        if not faces:
            return {"status": "no_face_detected"}
        if len(faces) > 1:
            return {"status": "multiple_faces_detected"}
        face_box = faces[0]
        if not self.validate_capture(image, face_box):
            return {"status": "invalid_capture"}
        x, y, width, height = face_box
        face = image[y : y + height, x : x + width]
        normalized = cv2.resize(face, (50, 50), interpolation=cv2.INTER_AREA)
        vector = (normalized.astype(np.float32).flatten() / 255.0).tolist()
        return {"status": "face_detected", "face_box": face_box, "embedding": vector}
