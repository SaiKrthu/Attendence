from collections.abc import Generator
from datetime import date, timedelta

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.models import FaceEmbedding, User, UserRole
from app.security import hash_password
from app.routes import employees as employee_routes
from app.routes import face_recognition
from app.routes import attendance as attendance_routes

TEST_FEATURE = [0.15] * 7500
SAMPLES = ["capture-one", "capture-two", "capture-three"]


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    app.state.test_session = test_session
    with test_session() as db:
        db.add(User(email="admin@example.com", password_hash=hash_password("admin-password-123"), role=UserRole.ADMIN))
        db.commit()

    def override_db() -> Generator[Session, None, None]:
        with test_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(employee_routes, "decode_capture", lambda _: np.zeros((100, 100, 3), dtype=np.uint8))
    monkeypatch.setattr(face_recognition, "decode_capture", lambda _: np.zeros((100, 100, 3), dtype=np.uint8))
    monkeypatch.setattr(attendance_routes, "decode_capture", lambda _: np.zeros((100, 100, 3), dtype=np.uint8))
    monkeypatch.setattr(employee_routes.face_service, "recognize", lambda _: {"status": "face_detected", "embedding": TEST_FEATURE})
    monkeypatch.setattr(face_recognition.face_service, "recognize", lambda _: {"status": "face_detected", "embedding": TEST_FEATURE})
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    del app.state.test_session
    Base.metadata.drop_all(engine)
    engine.dispose()


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health_and_empty_dashboard_never_fabricate_attendance(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}
    admin_token = login(client, "admin@example.com", "admin-password-123")
    summary = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert summary.status_code == 200
    assert summary.json() == {
        "total_employees": 0,
        "present_today": 0,
        "absent_today": 0,
        "late_today": 0,
        "on_leave": 0,
    }


def test_logout_revokes_the_jwt(client: TestClient) -> None:
    token = login(client, "admin@example.com", "admin-password-123")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_admin_auth_and_employee_enrollment_is_atomic(client: TestClient) -> None:
    assert client.get("/api/employees").status_code == 401
    admin_token = login(client, "admin@example.com", "admin-password-123")
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "employee_id": "EMP-1001",
        "full_name": "Example Employee",
        "email": "employee@example.com",
        "department": "Engineering",
        "designation": "Engineer",
        "joining_date": "2026-01-15",
        "password": "employee-password-123",
        "status": "active",
        "face_samples": SAMPLES,
    }
    response = client.post("/api/employees", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["face_registered"] is True
    assert client.get("/api/employees", headers=headers).status_code == 200

    with app.state.test_session() as db:
        encrypted = db.connection().exec_driver_sql("SELECT embedding FROM face_embeddings").scalars().all()
        assert len(encrypted) == 3
        assert all(vector.startswith(b"gAAAA") for vector in encrypted)
        assert len(db.query(FaceEmbedding).first().embedding) == len(TEST_FEATURE)

    employee_token = login(client, "employee@example.com", "employee-password-123")
    employee_headers = {"Authorization": f"Bearer {employee_token}"}
    recognition = client.post("/api/face/recognize", json={"image": "valid-capture"}, headers=employee_headers)
    assert recognition.status_code == 200
    assert recognition.json()["employee_id"] == "EMP-1001"
    assert client.get("/api/employees", headers=employee_headers).status_code == 403


def test_employee_signup_requires_admin_approval(client: TestClient) -> None:
    assert client.post(
        "/api/auth/signup",
        json={
            "employee_id": "EMP-ADMIN-EMAIL",
            "full_name": "Admin Email Collision",
            "email": "ADMIN@example.com",
            "department": "Operations",
            "password": "signup-password-789",
        },
    ).status_code == 409
    signup_payload = {
        "employee_id": "EMP-SIGNUP",
        "full_name": "New Applicant",
        "email": "new.applicant@example.com",
        "department": "Engineering",
        "designation": "Developer",
        "password": "signup-password-123",
    }
    submitted = client.post("/api/auth/signup", json=signup_payload)
    assert submitted.status_code == 201
    assert "approval" in submitted.json()["message"].lower()
    assert client.post(
        "/api/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    ).status_code == 401
    assert client.get("/api/signup-requests").status_code == 401

    admin_token = login(client, "admin@example.com", "admin-password-123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    request_list = client.get("/api/signup-requests", headers=admin_headers)
    assert request_list.status_code == 200
    request = request_list.json()["items"][0]
    assert request["email"] == signup_payload["email"]
    assert "password" not in request
    assert "password_hash" not in request
    assert client.post("/api/auth/signup", json=signup_payload).status_code == 409

    approved = client.post(f"/api/signup-requests/{request['id']}/approve", headers=admin_headers)
    assert approved.status_code == 200
    assert approved.json()["employee_id"] == signup_payload["employee_id"]
    assert approved.json()["face_registered"] is False
    employee_token = login(client, signup_payload["email"], signup_payload["password"])
    employee_headers = {"Authorization": f"Bearer {employee_token}"}
    assert client.get("/api/signup-requests", headers=employee_headers).status_code == 403
    assert client.get("/api/signup-requests", headers=admin_headers).json()["total"] == 0


def test_admin_can_reject_employee_signup(client: TestClient) -> None:
    signup_payload = {
        "employee_id": "EMP-REJECT",
        "full_name": "Rejected Applicant",
        "email": "rejected.applicant@example.com",
        "department": "Operations",
        "password": "signup-password-456",
    }
    submitted = client.post("/api/auth/signup", json=signup_payload)
    assert submitted.status_code == 201
    admin_token = login(client, "admin@example.com", "admin-password-123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    request_id = client.get("/api/signup-requests", headers=admin_headers).json()["items"][0]["id"]
    assert client.delete(f"/api/signup-requests/{request_id}", headers=admin_headers).status_code == 204
    assert client.post(
        "/api/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    ).status_code == 401
    assert client.get("/api/signup-requests", headers=admin_headers).json()["total"] == 0


def test_attendance_rejects_duplicate_daily_check_in(client: TestClient) -> None:
    admin_token = login(client, "admin@example.com", "admin-password-123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "employee_id": "EMP-1002",
        "full_name": "Attendance Employee",
        "email": "attendance@example.com",
        "department": "Operations",
        "joining_date": "2026-01-15",
        "password": "employee-password-456",
        "face_samples": SAMPLES,
    }
    assert client.post("/api/employees", json=payload, headers=admin_headers).status_code == 201
    employee_token = login(client, "attendance@example.com", "employee-password-456")
    headers = {"Authorization": f"Bearer {employee_token}"}
    first = client.post("/api/attendance/check-in", json={"image": "valid-capture"}, headers=headers)
    assert first.status_code == 201
    assert first.json()["employee_id"] == "EMP-1002"
    second = client.post("/api/attendance/check-in", json={"image": "valid-capture"}, headers=headers)
    assert second.status_code == 409
    assert "already marked" in second.json()["detail"].lower()


def test_admin_can_record_leave_and_absence(client: TestClient) -> None:
    admin_token = login(client, "admin@example.com", "admin-password-123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    employee_payload = {
        "employee_id": "EMP-STATUS",
        "full_name": "Status Employee",
        "email": "status@example.com",
        "department": "Operations",
        "joining_date": "2026-01-15",
        "password": "status-password-123",
        "face_samples": SAMPLES,
    }
    assert client.post("/api/employees", json=employee_payload, headers=admin_headers).status_code == 201
    today = date.today()
    leave = client.post(
        "/api/attendance/admin-status",
        json={"employee_id": "EMP-STATUS", "attendance_date": today.isoformat(), "status": "leave"},
        headers=admin_headers,
    )
    assert leave.status_code == 201
    assert leave.json()["status"] == "leave"
    duplicate = client.post(
        "/api/attendance/admin-status",
        json={"employee_id": "EMP-STATUS", "attendance_date": today.isoformat(), "status": "absent"},
        headers=admin_headers,
    )
    assert duplicate.status_code == 409
    summary = client.get("/api/dashboard/summary", headers=admin_headers).json()
    assert summary["on_leave"] == 1
    assert summary["absent_today"] == 0

    absence_date = today + timedelta(days=1)
    absent = client.post(
        "/api/attendance/admin-status",
        json={"employee_id": "EMP-STATUS", "attendance_date": absence_date.isoformat(), "status": "absent"},
        headers=admin_headers,
    )
    assert absent.status_code == 201
    assert absent.json()["status"] == "absent"
    employee_token = login(client, "status@example.com", "status-password-123")
    forbidden = client.post(
        "/api/attendance/admin-status",
        json={"employee_id": "EMP-STATUS", "attendance_date": absence_date.isoformat(), "status": "absent"},
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert forbidden.status_code == 403


def test_invalid_enrollment_does_not_create_partial_employee(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_token = login(client, "admin@example.com", "admin-password-123")
    headers = {"Authorization": f"Bearer {admin_token}"}
    monkeypatch.setattr(
        employee_routes.face_service,
        "recognize",
        lambda _: {"status": "multiple_faces_detected"},
    )
    response = client.post(
        "/api/employees",
        headers=headers,
        json={
            "employee_id": "EMP-INVALID",
            "full_name": "Rejected Enrollment",
            "email": "rejected@example.com",
            "department": "Engineering",
            "joining_date": "2026-01-15",
            "password": "employee-password-789",
            "face_samples": SAMPLES,
        },
    )
    assert response.status_code == 422
    assert client.get("/api/employees", headers=headers).json()["total"] == 0


def test_face_detector_equalizes_webcam_frame_and_uses_finer_scale(monkeypatch: pytest.MonkeyPatch) -> None:
    class RecordingCascade:
        def detectMultiScale(self, image: np.ndarray, **options: object) -> list[tuple[int, int, int, int]]:
            assert np.array_equal(image, cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)))
            assert options == {"scaleFactor": 1.1, "minNeighbors": 4, "minSize": (60, 60)}
            return [(120, 80, 140, 140)]

    frame = np.full((480, 640, 3), 127, dtype=np.uint8)
    monkeypatch.setattr(face_recognition.face_service, "face_cascade", RecordingCascade())
    assert face_recognition.face_service.detect_faces(frame) == [(120, 80, 140, 140)]
