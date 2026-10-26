from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.dependencies import get_current_user, get_db, require_admin
from app.models import Attendance, AttendanceStatus, Employee, EmployeeStatus, User, UserRole
from app.routes.face_recognition import decode_capture, match_face
from app.schemas.attendance import (
    AttendanceResponse,
    AttendanceStatusRequest,
    CheckInRequest,
    CheckOutRequest,
)

router = APIRouter()


def local_now() -> datetime:
    return datetime.now(ZoneInfo(get_settings().timezone))


def to_response(record: Attendance) -> AttendanceResponse:
    return AttendanceResponse(
        id=record.id,
        employee_id=record.employee.employee_id,
        employee_name=record.employee_name,
        attendance_date=record.attendance_date,
        check_in_time=record.check_in_time.isoformat() if record.check_in_time else None,
        check_out_time=record.check_out_time.isoformat() if record.check_out_time else None,
        status=record.status.value,
        working_hours=record.working_hours,
    )


def resolve_employee_for_capture(payload_image: str | None, user: User, db: Session) -> Employee:
    if user.role == UserRole.EMPLOYEE:
        if user.employee is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is not linked to an employee.")
        employee = user.employee
        if payload_image:
            matched, _ = match_face(decode_capture(payload_image), db)
            if matched.id != employee.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The captured face does not match this account.")
        return employee
    if not payload_image:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="A face capture is required for an administrator attendance action.")
    employee, _ = match_face(decode_capture(payload_image), db)
    return employee


@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def check_in(
    payload: CheckInRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AttendanceResponse:
    employee = resolve_employee_for_capture(payload.image, user, db)
    if employee.status != EmployeeStatus.ACTIVE or not employee.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive employees cannot mark attendance.")
    now = local_now()
    existing = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.attendance_date == now.date(),
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Attendance already marked for today.")
    work_start = datetime.strptime(get_settings().work_start_time, "%H:%M").time()
    late_boundary = (datetime.combine(now.date(), work_start) + timedelta(minutes=get_settings().late_after_minutes)).time()
    record = Attendance(
        employee_id=employee.id,
        employee_name=employee.full_name,
        attendance_date=now.date(),
        check_in_time=now.time().replace(tzinfo=None, microsecond=0),
        status=AttendanceStatus.LATE if now.time().replace(tzinfo=None) > late_boundary else AttendanceStatus.PRESENT,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        conflict = db.query(Attendance).filter(
            Attendance.employee_id == employee.id,
            Attendance.attendance_date == now.date(),
        ).first()
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Attendance already marked for today.")
        raise
    db.refresh(record)
    return to_response(record)


@router.post("/check-out", response_model=AttendanceResponse)
def check_out(
    payload: CheckOutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AttendanceResponse:
    employee = resolve_employee_for_capture(payload.image, user, db)
    now = local_now()
    record = db.query(Attendance).options(joinedload(Attendance.employee)).filter(
        Attendance.employee_id == employee.id,
        Attendance.attendance_date == now.date(),
    ).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No check-in record exists for today.")
    if record.check_out_time is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Check-out is already recorded for today.")
    record.check_out_time = now.time().replace(tzinfo=None, microsecond=0)
    check_in_datetime = datetime.combine(record.attendance_date, record.check_in_time)
    check_out_datetime = datetime.combine(record.attendance_date, record.check_out_time)
    record.working_hours = round(max(0.0, (check_out_datetime - check_in_datetime).total_seconds() / 3600), 2)
    if record.working_hours < 4:
        record.status = AttendanceStatus.HALF_DAY
    db.commit()
    db.refresh(record)
    return to_response(record)


@router.post("/admin-status", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def record_admin_status(
    payload: AttendanceStatusRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> AttendanceResponse:
    employee = db.query(Employee).filter(Employee.employee_id == payload.employee_id.strip()).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    existing = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.attendance_date == payload.attendance_date,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An attendance record already exists for this employee and date.",
        )
    record = Attendance(
        employee_id=employee.id,
        employee_name=employee.full_name,
        attendance_date=payload.attendance_date,
        status=AttendanceStatus(payload.status),
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An attendance record already exists for this employee and date.",
        ) from error
    db.refresh(record)
    return to_response(record)


@router.get("", response_model=list[AttendanceResponse])
def list_attendance(
    attendance_date: str | None = Query(None, alias="date"),
    attendance_status: AttendanceStatus | None = Query(None, alias="status"),
    employee_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AttendanceResponse]:
    query = db.query(Attendance).join(Employee).options(joinedload(Attendance.employee))
    if user.role == UserRole.EMPLOYEE:
        if user.employee is None:
            return []
        query = query.filter(Attendance.employee_id == user.employee.id)
    elif employee_id:
        query = query.filter(Employee.employee_id == employee_id)
    if attendance_date:
        try:
            parsed_date = datetime.strptime(attendance_date, "%Y-%m-%d").date()
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Date must use YYYY-MM-DD format.") from error
        query = query.filter(Attendance.attendance_date == parsed_date)
    if attendance_status:
        query = query.filter(Attendance.status == attendance_status)
    return [to_response(record) for record in query.order_by(Attendance.attendance_date.desc(), Attendance.check_in_time.desc()).limit(500).all()]


@router.get("/today", response_model=list[AttendanceResponse])
def attendance_today(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AttendanceResponse]:
    query = db.query(Attendance).options(joinedload(Attendance.employee)).filter(
        Attendance.attendance_date == local_now().date()
    )
    if user.role == UserRole.EMPLOYEE:
        if user.employee is None:
            return []
        query = query.filter(Attendance.employee_id == user.employee.id)
    return [to_response(record) for record in query.order_by(Attendance.check_in_time).all()]


@router.get("/employee/{employee_id}", response_model=list[AttendanceResponse])
def employee_attendance(
    employee_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AttendanceResponse]:
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    if user.role == UserRole.EMPLOYEE and (user.employee is None or user.employee.id != employee.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only view your own attendance history.")
    records = db.query(Attendance).options(joinedload(Attendance.employee)).filter(
        Attendance.employee_id == employee.id
    ).order_by(Attendance.attendance_date.desc()).limit(365).all()
    return [to_response(record) for record in records]
