from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CheckInRequest(BaseModel):
    image: str = Field(min_length=1, max_length=1_500_000)


class CheckOutRequest(BaseModel):
    image: str | None = Field(default=None, max_length=1_500_000)


class AttendanceStatusRequest(BaseModel):
    employee_id: str = Field(min_length=1, max_length=50)
    attendance_date: date
    status: Literal["absent", "leave"]


class AttendanceResponse(BaseModel):
    id: int
    employee_id: str
    employee_name: str
    attendance_date: date
    check_in_time: str | None
    check_out_time: str | None
    status: str
    working_hours: float | None


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Department name cannot be blank.")
        return value


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: str | None
