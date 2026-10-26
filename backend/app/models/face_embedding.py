from __future__ import annotations

from datetime import datetime

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.config import get_settings


class EncryptedEmbedding(TypeDecorator[list[float]]):
    impl = LargeBinary
    cache_ok = True

    @staticmethod
    def _fernet() -> Fernet:
        configured_key = get_settings().face_encryption_key
        key = configured_key.encode() if configured_key else base64.urlsafe_b64encode(
            hashlib.sha256(b"attendance-face-embedding:" + get_settings().secret_key.encode()).digest()
        )
        try:
            return Fernet(key)
        except ValueError as error:
            raise ValueError("FACE_ENCRYPTION_KEY must be a valid URL-safe 32-byte Fernet key.") from error

    def process_bind_param(self, value: list[float] | None, dialect: Any) -> bytes | None:
        if value is None:
            return None
        serialized = json.dumps(value, separators=(",", ":")).encode()
        return self._fernet().encrypt(serialized)

    def process_result_value(self, value: bytes | None, dialect: Any) -> list[float] | None:
        if value is None:
            return None
        try:
            return json.loads(self._fernet().decrypt(value))
        except (InvalidToken, ValueError, json.JSONDecodeError) as error:
            raise ValueError("Stored face embedding could not be decrypted.") from error


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    embedding: Mapped[list[float]] = mapped_column(EncryptedEmbedding(), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    employee: Mapped["Employee"] = relationship(back_populates="face_embeddings")
