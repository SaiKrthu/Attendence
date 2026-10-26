import argparse
import getpass
import sys

from app.config import get_settings
from app.database import SessionLocal
from app.models import User, UserRole
from app.security import hash_password


def create_admin() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Create the first attendance-system administrator.")
    parser.add_argument("--email", default=settings.admin_email)
    args = parser.parse_args()
    password = settings.admin_password or getpass.getpass("New admin password (minimum 12 characters): ")
    if len(password) < 12:
        print("Admin password must contain at least 12 characters.", file=sys.stderr)
        raise SystemExit(2)
    with SessionLocal() as db:
        existing = db.query(User).filter(User.email == args.email).first()
        if existing is not None:
            print(f"An account already exists for {args.email}.", file=sys.stderr)
            raise SystemExit(2)
        db.add(User(email=args.email, password_hash=hash_password(password), role=UserRole.ADMIN))
        db.commit()
    print(f"Administrator account created for {args.email}.")


if __name__ == "__main__":
    create_admin()
