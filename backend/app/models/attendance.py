from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    LEAVE = "leave"
    HALF_DAY = "half_day"


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    employee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    check_in_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    check_out_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(AttendanceStatus, values_callable=lambda enum: [item.value for item in enum]),
        default=AttendanceStatus.PRESENT,
        nullable=False,
    )
    working_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    employee: Mapped["Employee"] = relationship(back_populates="attendance_records")
