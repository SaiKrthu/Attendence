from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import TypedDict

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

password_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__rounds=310_000,
)


class AccessTokenClaims(TypedDict):
    sub: str
    role: str
    jti: str
    exp: int


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(subject: str, role: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": subject, "role": role, "jti": token_urlsafe(32), "exp": expires_at},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_access_token(token: str) -> AccessTokenClaims:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as error:
        raise ValueError("Invalid or expired access token.") from error
    subject = payload.get("sub")
    role = payload.get("role")
    token_id = payload.get("jti")
    expiration = payload.get("exp")
    if (
        not isinstance(subject, str)
        or not isinstance(role, str)
        or not isinstance(token_id, str)
        or not isinstance(expiration, int)
    ):
        raise ValueError("Invalid token claims.")
    return {"sub": subject, "role": role, "jti": token_id, "exp": expiration}
