from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[EmployeeStatus] = mapped_column(
        SAEnum(EmployeeStatus, values_callable=lambda enum: [item.value for item in enum]),
        default=EmployeeStatus.ACTIVE,
        nullable=False,
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User | None"] = relationship(back_populates="employee")
    department: Mapped["Department | None"] = relationship(back_populates="employees")
    face_embeddings: Mapped[list["FaceEmbedding"]] = relationship(back_populates="employee")
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="employee")
