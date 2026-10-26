from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dependencies import get_db, require_admin
from app.models import Attendance, AttendanceStatus, Employee, EmployeeStatus, User

router = APIRouter()


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict[str, int]:
    today = datetime.now(ZoneInfo(get_settings().timezone)).date()
    active_employees = db.query(func.count(Employee.id)).filter(
        Employee.status == EmployeeStatus.ACTIVE, Employee.is_active.is_(True)
    ).scalar() or 0
    present_today = db.query(func.count(Attendance.id)).filter(
        Attendance.attendance_date == today,
        Attendance.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]),
    ).scalar() or 0
    late_today = db.query(func.count(Attendance.id)).filter(
        Attendance.attendance_date == today, Attendance.status == AttendanceStatus.LATE
    ).scalar() or 0
    on_leave = db.query(func.count(Attendance.id)).filter(
        Attendance.attendance_date == today, Attendance.status == AttendanceStatus.LEAVE
    ).scalar() or 0
    absent_today = max(active_employees - present_today - on_leave, 0)
    return {
        "total_employees": active_employees,
        "present_today": present_today,
        "absent_today": absent_today,
        "late_today": late_today,
        "on_leave": on_leave,
    }
