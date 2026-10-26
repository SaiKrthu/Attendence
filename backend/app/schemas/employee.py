from datetime import date

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmployeeCreate(BaseModel):
    employee_id: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    department: str = Field(min_length=1, max_length=150)
    designation: str | None = Field(default=None, max_length=150)
    joining_date: date
    password: str = Field(min_length=10, max_length=128)
    status: Literal["active", "inactive"] = "active"
    face_samples: list[str] = Field(min_length=3, max_length=10)

    @field_validator("employee_id", "full_name", "department")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("face_samples")
    @classmethod
    def validate_sample_sizes(cls, samples: list[str]) -> list[str]:
        if any(len(sample) > 1_500_000 for sample in samples):
            raise ValueError("Each face sample must be no larger than 1.5 MB when base64 encoded.")
        return samples


class EmployeeUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    department: str = Field(min_length=1, max_length=150)
    designation: str | None = Field(default=None, max_length=150)
    joining_date: date

    @field_validator("full_name", "department")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


class EmployeeStatusUpdate(BaseModel):
    status: Literal["active", "inactive"]


class EmployeeResponse(BaseModel):
    id: int
    employee_id: str
    full_name: str
    email: str
    phone: str | None
    department: str | None
    designation: str | None
    joining_date: date
    status: str
    face_registered: bool
