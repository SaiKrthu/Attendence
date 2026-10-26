from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.dependencies import get_db, require_admin
from app.models import Department, Employee, EmployeeStatus, FaceEmbedding, User, UserRole
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeStatusUpdate, EmployeeUpdate
from app.schemas.face import FaceSamplesRequest
from app.security import hash_password
from app.routes.face_recognition import decode_capture, face_service

router = APIRouter()


def employee_response(employee: Employee) -> EmployeeResponse:
    return EmployeeResponse(
        id=employee.id,
        employee_id=employee.employee_id,
        full_name=employee.full_name,
        email=employee.email,
        phone=employee.phone,
        department=employee.department.name if employee.department else None,
        designation=employee.designation,
        joining_date=employee.joining_date,
        status=employee.status.value,
        face_registered=bool(employee.face_embeddings),
    )


@router.get("", response_model=dict[str, Any])
def list_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
    department: str | None = Query(None),
    employee_status: EmployeeStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    query = db.query(Employee).options(joinedload(Employee.department), joinedload(Employee.face_embeddings))
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(or_(Employee.employee_id.ilike(pattern), Employee.full_name.ilike(pattern), Employee.email.ilike(pattern)))
    if department:
        query = query.join(Employee.department).filter(Department.name == department)
    if employee_status:
        query = query.filter(Employee.status == employee_status)
    total = query.count()
    employees = query.order_by(Employee.full_name).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [employee_response(employee) for employee in employees], "page": page, "page_size": page_size, "total": total}


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> EmployeeResponse:
    embeddings = validate_face_samples(payload.face_samples)
    try:
        employee_status = EmployeeStatus(payload.status)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Status must be active or inactive.") from error
    if db.query(Employee).filter(or_(Employee.employee_id == payload.employee_id, Employee.email == payload.email)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee ID or email is already registered.")
    department = db.query(Department).filter(Department.name == payload.department.strip()).first()
    if department is None:
        department = Department(name=payload.department.strip())
        db.add(department)
        db.flush()
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.EMPLOYEE,
        is_active=employee_status == EmployeeStatus.ACTIVE,
    )
    employee = Employee(
        employee_id=payload.employee_id.strip(),
        full_name=payload.full_name.strip(),
        email=payload.email,
        phone=payload.phone,
        designation=payload.designation,
        joining_date=payload.joining_date,
        status=employee_status,
        is_active=employee_status == EmployeeStatus.ACTIVE,
        department=department,
        user=user,
    )
    db.add(employee)
    try:
        db.flush()
        db.add_all(
            FaceEmbedding(employee_id=employee.id, embedding=embedding, sample_count=len(embeddings), source="browser_camera")
            for embedding in embeddings
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee ID or email is already registered.") from error
    db.refresh(employee)
    return employee_response(employee)


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> EmployeeResponse:
    employee = db.query(Employee).options(joinedload(Employee.department), joinedload(Employee.face_embeddings)).filter(
        Employee.employee_id == employee_id
    ).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    return employee_response(employee)


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> EmployeeResponse:
    employee = db.query(Employee).options(joinedload(Employee.department), joinedload(Employee.face_embeddings)).filter(
        Employee.employee_id == employee_id
    ).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    duplicate = db.query(Employee).filter(Employee.email == payload.email, Employee.id != employee.id).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already used by another employee.")
    department = db.query(Department).filter(Department.name == payload.department.strip()).first()
    if department is None:
        department = Department(name=payload.department.strip())
        db.add(department)
    employee.full_name = payload.full_name.strip()
    employee.email = payload.email
    employee.phone = payload.phone
    employee.designation = payload.designation
    employee.joining_date = payload.joining_date
    employee.department = department
    if employee.user:
        employee.user.email = payload.email
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.") from error
    db.refresh(employee)
    return employee_response(employee)


@router.patch("/{employee_id}/status", response_model=EmployeeResponse)
def patch_employee_status(
    employee_id: str,
    payload: EmployeeStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> EmployeeResponse:
    try:
        new_status = EmployeeStatus(payload.status)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Status must be active or inactive.") from error
    employee = db.query(Employee).options(joinedload(Employee.department), joinedload(Employee.face_embeddings)).filter(
        Employee.employee_id == employee_id
    ).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    employee.status = new_status
    employee.is_active = new_status == EmployeeStatus.ACTIVE
    if employee.user:
        employee.user.is_active = employee.is_active
    db.commit()
    db.refresh(employee)
    return employee_response(employee)


@router.post("/{employee_id}/face/register", status_code=status.HTTP_201_CREATED)
def register_face(
    employee_id: str,
    payload: FaceSamplesRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    embeddings = validate_face_samples(payload.samples)
    db.query(FaceEmbedding).filter(FaceEmbedding.employee_id == employee.id).delete()
    db.add_all(
        FaceEmbedding(employee_id=employee.id, embedding=embedding, sample_count=len(embeddings), source="browser_camera")
        for embedding in embeddings
    )
    db.commit()
    return {"employee_id": employee.employee_id, "samples_registered": len(embeddings), "raw_images_stored": False}


def validate_face_samples(samples: list[str]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for sample_number, sample in enumerate(samples, start=1):
        image = decode_capture(sample)
        result = face_service.recognize(image)
        if result["status"] != "face_detected":
            guidance = {
                "no_face_detected": "Face the camera, move closer, and use brighter, even lighting.",
                "multiple_faces_detected": "Ensure only the employee being enrolled is visible.",
                "invalid_capture": "Hold still and capture a sharp, well-lit image.",
            }.get(result["status"], "Capture a clear image of exactly one face.")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Face sample {sample_number} rejected: {result['status']}. {guidance}",
            )
        embeddings.append(result["embedding"])
    return embeddings
