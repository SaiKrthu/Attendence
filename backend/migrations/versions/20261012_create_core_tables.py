"""Create core attendance database tables.

Revision ID: 202610120001
Revises: 
Create Date: 2026-10-12 16:17:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "202610120001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "employee", name="userrole"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_departments_id"), "departments", ["id"], unique=False)
    op.create_index(op.f("ix_departments_name"), "departments", ["name"], unique=True)

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("designation", sa.String(length=150), nullable=True),
        sa.Column("joining_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "inactive", name="employeestatus"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_employees_email"), "employees", ["email"], unique=True)
    op.create_index(op.f("ix_employees_employee_id"), "employees", ["employee_id"], unique=True)
    op.create_index(op.f("ix_employees_id"), "employees", ["id"], unique=False)

    op.create_table(
        "face_embeddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.LargeBinary(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_face_embeddings_employee_id"), "face_embeddings", ["employee_id"], unique=False)
    op.create_index(op.f("ix_face_embeddings_id"), "face_embeddings", ["id"], unique=False)

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("employee_name", sa.String(length=200), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("check_in_time", sa.Time(), nullable=True),
        sa.Column("check_out_time", sa.Time(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("present", "late", "absent", "leave", "half_day", name="attendancestatus"),
            nullable=False,
        ),
        sa.Column("working_hours", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),
    )
    op.create_index(op.f("ix_attendance_attendance_date"), "attendance", ["attendance_date"], unique=False)
    op.create_index(op.f("ix_attendance_employee_id"), "attendance", ["employee_id"], unique=False)
    op.create_index(op.f("ix_attendance_id"), "attendance", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_attendance_id"), table_name="attendance")
    op.drop_index(op.f("ix_attendance_employee_id"), table_name="attendance")
    op.drop_index(op.f("ix_attendance_attendance_date"), table_name="attendance")
    op.drop_table("attendance")

    op.drop_index(op.f("ix_face_embeddings_id"), table_name="face_embeddings")
    op.drop_index(op.f("ix_face_embeddings_employee_id"), table_name="face_embeddings")
    op.drop_table("face_embeddings")

    op.drop_index(op.f("ix_employees_id"), table_name="employees")
    op.drop_index(op.f("ix_employees_employee_id"), table_name="employees")
    op.drop_index(op.f("ix_employees_email"), table_name="employees")
    op.drop_table("employees")

    op.drop_index(op.f("ix_departments_name"), table_name="departments")
    op.drop_index(op.f("ix_departments_id"), table_name="departments")
    op.drop_table("departments")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
