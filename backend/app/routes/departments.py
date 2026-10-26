from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_admin
from app.models import Department, User
from app.schemas.attendance import DepartmentCreate, DepartmentResponse

router = APIRouter()


@router.get("", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[Department]:
    return db.query(Department).order_by(Department.name).all()


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Department:
    department = Department(name=payload.name.strip(), description=payload.description)
    db.add(department)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department name already exists.") from error
    db.refresh(department)
    return department
