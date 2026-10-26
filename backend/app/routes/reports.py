import csv
from datetime import date
from io import StringIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_admin
from app.models import Attendance, Department, Employee, User

router = APIRouter()


def spreadsheet_safe(value: str) -> str:
    if value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


@router.get("/attendance")
def attendance_report(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    department: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> StreamingResponse:
    query = db.query(Attendance, Employee).join(Employee)
    if start_date:
        query = query.filter(Attendance.attendance_date >= start_date)
    if end_date:
        query = query.filter(Attendance.attendance_date <= end_date)
    if department:
        query = query.join(Department).filter(Department.name == department)
    results = query.order_by(Attendance.attendance_date, Employee.employee_id).all()
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Employee ID", "Employee Name", "Date", "Check-in", "Check-out", "Status", "Working Hours"])
    for attendance, employee in results:
        writer.writerow([
            spreadsheet_safe(employee.employee_id),
            spreadsheet_safe(attendance.employee_name),
            attendance.attendance_date.isoformat(),
            attendance.check_in_time.isoformat() if attendance.check_in_time else "",
            attendance.check_out_time.isoformat() if attendance.check_out_time else "",
            spreadsheet_safe(attendance.status.value),
            attendance.working_hours if attendance.working_hours is not None else "",
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="attendance-report.csv"'},
    )
