from __future__ import annotations

from functools import lru_cache
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Employee Attendance Management API"
    environment: Literal["development", "test", "production"] = "development"
    api_prefix: str = "/api"
    frontend_origins: str = "http://localhost:3000"
    database_url: str = "sqlite:///./attendance.db"
    secret_key: str = "dev-only-change-this-secret-before-deploying"
    face_encryption_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    admin_email: str = "admin@example.com"
    admin_password: str = ""
    work_start_time: str = "09:00"
    late_after_minutes: int = 15
    timezone: str = "Asia/Dhaka"

    @field_validator("work_start_time")
    @classmethod
    def validate_work_start_time(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError as error:
            raise ValueError("WORK_START_TIME must use HH:MM format.") from error
        return value

    @field_validator("late_after_minutes")
    @classmethod
    def validate_late_after_minutes(cls, value: int) -> int:
        if value < 0 or value > 240:
            raise ValueError("LATE_AFTER_MINUTES must be between 0 and 240.")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("TIMEZONE must be a valid IANA time zone.") from error
        return value

    @property
    def cors_origins(self) -> list[str]:
        origins = []
        for origin in self.frontend_origins.split(","):
            cleaned = origin.strip().rstrip("/")
            if cleaned:
                origins.append(cleaned)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
