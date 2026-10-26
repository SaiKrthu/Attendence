from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import bearer_scheme, get_current_user, get_db
from app.models import Employee, EmployeeSignup, RevokedToken, User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.schemas.employee_signup import EmployeeSignupCreate
from app.security import create_access_token, decode_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: EmployeeSignupCreate, db: Session = Depends(get_db)) -> dict[str, str]:
    existing_employee = db.query(Employee.id).filter(
        or_(
            Employee.employee_id == payload.employee_id,
            func.lower(Employee.email) == payload.email,
        )
    ).first()
    existing_signup = db.query(EmployeeSignup.id).filter(
        or_(
            EmployeeSignup.employee_id == payload.employee_id,
            EmployeeSignup.email == payload.email,
        )
    ).first()
    existing_user = db.query(User.id).filter(func.lower(User.email) == payload.email).first()
    if existing_employee or existing_signup or existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That employee ID or email is already registered or awaiting review.",
        )
    request = EmployeeSignup(
        employee_id=payload.employee_id,
        full_name=payload.full_name,
        email=payload.email,
        department=payload.department,
        designation=payload.designation,
        password_hash=hash_password(payload.password),
    )
    db.add(request)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That employee ID or email is already registered or awaiting review.",
        ) from error
    return {"message": "Your registration has been submitted for administrator approval."}


def user_response(user: User) -> UserResponse:
    employee = user.employee
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        employee_id=employee.employee_id if employee else None,
        full_name=employee.full_name if employee else None,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect.")
    return LoginResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        user=user_response(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    claims = decode_access_token(credentials.credentials)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.query(RevokedToken).filter(RevokedToken.expires_at <= now).delete(synchronize_session=False)
    db.add(
        RevokedToken(
            token_id=claims["jti"],
            expires_at=datetime.fromtimestamp(claims["exp"], timezone.utc).replace(tzinfo=None),
        )
    )
    db.commit()
    return None


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return user_response(user)
