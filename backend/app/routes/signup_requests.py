from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_admin
from app.models import Department, Employee, EmployeeSignup, EmployeeStatus, User, UserRole
from app.routes.employees import employee_response
from app.schemas.employee import EmployeeResponse
from app.schemas.employee_signup import EmployeeSignupResponse

router = APIRouter()


def signup_response(request: EmployeeSignup) -> EmployeeSignupResponse:
    return EmployeeSignupResponse(
        id=request.id,
        employee_id=request.employee_id,
        full_name=request.full_name,
        email=request.email,
        department=request.department,
        designation=request.designation,
        created_at=request.created_at,
    )


@router.get("", response_model=dict[str, object])
def list_signup_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, object]:
    query = db.query(EmployeeSignup)
    total = query.count()
    requests = query.order_by(EmployeeSignup.created_at, EmployeeSignup.id).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return {
        "items": [signup_response(request) for request in requests],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post("/{request_id}/approve", response_model=EmployeeResponse)
def approve_signup(
    request_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> EmployeeResponse:
    request = db.get(EmployeeSignup, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signup request not found.")

    existing = db.query(Employee.id).filter(
        or_(
            Employee.employee_id == request.employee_id,
            func.lower(Employee.email) == request.email,
        )
    ).first()
    existing_user = db.query(User.id).filter(func.lower(User.email) == request.email).first()
    if existing or existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The employee ID or email is already in use. Reject this request and submit corrected details.",
        )

    department = db.query(Department).filter(Department.name == request.department).first()
    if department is None:
        department = Department(name=request.department)
        db.add(department)
        db.flush()

    user = User(
        email=request.email,
        password_hash=request.password_hash,
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    employee = Employee(
        employee_id=request.employee_id,
        full_name=request.full_name,
        email=request.email,
        designation=request.designation,
        joining_date=date.today(),
        status=EmployeeStatus.ACTIVE,
        is_active=True,
        department=department,
        user=user,
    )
    db.add(employee)
    db.delete(request)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The employee ID or email is already in use.",
        ) from error
    db.refresh(employee)
    return employee_response(employee)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def reject_signup(
    request_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Response:
    request = db.get(EmployeeSignup, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signup request not found.")
    db.delete(request)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
