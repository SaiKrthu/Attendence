from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cryptography.fernet import Fernet

from app.config import get_settings
from app.routes.attendance import router as attendance_router
from app.routes.auth import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.departments import router as departments_router
from app.routes.employees import router as employees_router
from app.routes.face_recognition import router as face_router
from app.routes.health import router as health_router
from app.routes.reports import router as reports_router
from app.routes.signup_requests import router as signup_requests_router

settings = get_settings()

if "*" in settings.cors_origins:
    raise ValueError("FRONTEND_ORIGINS must list explicit origins; '*' is not allowed.")

is_production = settings.environment == "production"
if is_production:
    if len(settings.secret_key) < 32 or settings.secret_key.startswith("dev-only"):
        raise ValueError("Set a unique SECRET_KEY with at least 32 characters in production.")
    if not settings.face_encryption_key:
        raise ValueError("Set FACE_ENCRYPTION_KEY to a Fernet key in production.")
    Fernet(settings.face_encryption_key.encode())

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=f"{settings.api_prefix}/auth")
app.include_router(signup_requests_router, prefix=f"{settings.api_prefix}/signup-requests")
app.include_router(employees_router, prefix=f"{settings.api_prefix}/employees")
app.include_router(departments_router, prefix=f"{settings.api_prefix}/departments")
app.include_router(face_router, prefix=f"{settings.api_prefix}/face")
app.include_router(attendance_router, prefix=f"{settings.api_prefix}/attendance")
app.include_router(dashboard_router, prefix=f"{settings.api_prefix}/dashboard")
app.include_router(reports_router, prefix=f"{settings.api_prefix}/reports")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Employee Attendance Management API is running."}
