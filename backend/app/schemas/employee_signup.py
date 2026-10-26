from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmployeeSignupCreate(BaseModel):
    employee_id: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    department: str = Field(min_length=1, max_length=150)
    designation: str | None = Field(default=None, max_length=150)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("employee_id", "full_name", "department", mode="before")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("designation")
    @classmethod
    def normalize_designation(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class EmployeeSignupResponse(BaseModel):
    id: int
    employee_id: str
    full_name: str
    email: EmailStr
    department: str
    designation: str | None
    created_at: datetime
