# Attendance API

FastAPI backend for the employee attendance application. It uses SQLAlchemy and
Alembic, supports PostgreSQL for deployment, and defaults to a local SQLite
database so the project can be run without installing a database server.

## Local setup (Windows PowerShell)

Use Python 3.10 or newer.

From the repository root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m alembic upgrade head
python -m app.cli
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The admin setup command prompts for the initial admin password. Use at least 12
characters. It stores only a salted PBKDF2 hash. Do not set `ADMIN_PASSWORD` in
a deployed environment unless your deployment system securely manages it.

Run the API integration tests with:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Expected local addresses:

- API health: `http://127.0.0.1:8000/api/health`
- Interactive API docs: `http://127.0.0.1:8000/docs`

## API capabilities

- JWT login, database-backed logout revocation, current user, role-aware access checks
- Admin employee creation/editing/deactivation and department management
- Public employee sign-up requests with admin-only review and approval
- Employee creation and face enrollment in one transaction
- Haar Cascade face validation with the legacy 50×50 KNN-style pixel feature representation
- Face matching and authenticated daily check-in/check-out
- Unique employee/date attendance constraint, late calculation, half-day hours
- Admin-recorded absent/leave statuses, with one attendance record per employee/date
- Dashboard summary and CSV attendance export
- Encrypted face feature vectors; submitted camera images are processed in memory and not saved

Face recognition is a lightweight continuation of the legacy prototype, not a
liveness or anti-spoofing system. Do not use it as the sole control for
high-risk decisions. A stronger face embedding/liveness provider can replace
the recognition service without changing the API payload contract.

## Production database and secrets

Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL, for example:

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

Never commit `.env`. Production must configure:

- `ENVIRONMENT=production`
- a unique `SECRET_KEY` of at least 32 characters
- `FACE_ENCRYPTION_KEY` generated with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `DATABASE_URL` for hosted PostgreSQL
- `FRONTEND_ORIGINS` set to exact HTTPS frontend origin(s), without `*`

Back up `FACE_ENCRYPTION_KEY` securely and keep it unchanged: existing
encrypted face vectors cannot be read after losing or rotating that key.

Run migrations as a release step with `python -m alembic upgrade head`, then
start the API with `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
Use HTTPS at the hosting provider/reverse proxy; browser camera APIs require
HTTPS except on localhost.

Attendance settings can be configured with `WORK_START_TIME` (`HH:MM`),
`LATE_AFTER_MINUTES`, and `TIMEZONE` (IANA zone, default `Asia/Dhaka`).
