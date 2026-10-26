import base64
import binascii

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sklearn.neighbors import KNeighborsClassifier
from sqlalchemy.orm import Session, joinedload

from app.dependencies import get_current_user, get_db
from app.models import Employee, EmployeeStatus, FaceEmbedding, User
from app.schemas.face import FaceImageRequest
from app.services.face_recognition_service import FaceRecognitionService

router = APIRouter()
face_service = FaceRecognitionService()
MAX_IMAGE_BYTES = 1_000_000
MATCH_DISTANCE_THRESHOLD = 0.22


def decode_capture(image_data: str) -> np.ndarray:
    encoded = image_data.split(",", 1)[1] if image_data.startswith("data:image/") else image_data
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Image must be valid base64.") from error
    if not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is empty or exceeds 1 MB.")
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None or image.shape[0] > 2400 or image.shape[1] > 2400:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Image format or dimensions are invalid.")
    return image


def match_face(image: np.ndarray, db: Session) -> tuple[Employee, float]:
    detection = face_service.recognize(image)
    if detection["status"] != "face_detected":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Face validation failed: {detection['status']}. Ensure one well-lit face is visible.",
        )
    incoming = np.asarray(detection["embedding"], dtype=np.float32)
    records = (
        db.query(FaceEmbedding, Employee)
        .join(Employee, Employee.id == FaceEmbedding.employee_id)
        .options(joinedload(FaceEmbedding.employee))
        .filter(Employee.status == EmployeeStatus.ACTIVE, Employee.is_active.is_(True))
        .all()
    )
    if not records:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active employee face profiles are registered.")
    features: list[np.ndarray] = []
    labels: list[int] = []
    records_by_employee: dict[int, Employee] = {}
    for record, employee in records:
        vector = np.asarray(record.embedding, dtype=np.float32)
        if vector.shape == incoming.shape:
            features.append(vector)
            labels.append(employee.id)
            records_by_employee[employee.id] = employee
    if not features:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No compatible face profiles are registered.")
    classifier = KNeighborsClassifier(n_neighbors=min(5, len(features)), weights="distance", metric="manhattan")
    classifier.fit(np.stack(features), np.asarray(labels))
    distances, _ = classifier.kneighbors(incoming.reshape(1, -1), n_neighbors=min(5, len(features)))
    best_distance = float(distances[0][0] / incoming.size)
    if best_distance > MATCH_DISTANCE_THRESHOLD:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Face not recognized.")
    matched_id = int(classifier.predict(incoming.reshape(1, -1))[0])
    employee = records_by_employee.get(matched_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Face not recognized.")
    return employee, best_distance


@router.post("/recognize")
def recognize(
    payload: FaceImageRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, object]:
    employee, distance = match_face(decode_capture(payload.image), db)
    return {
        "employee_id": employee.employee_id,
        "full_name": employee.full_name,
        "department": employee.department.name if employee.department else None,
        "confidence": round(max(0.0, 1.0 - distance / MATCH_DISTANCE_THRESHOLD), 3),
    }
