"""Add summary verification and doctor edit audit tables

Revision ID: 002_verification_and_audit
Revises: 001_initial_schema
Create Date: 2026-09-06 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_verification_and_audit"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Summary Verifications Table
    op.create_table(
        "summary_verifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("verification_id", sa.String(length=50), nullable=False),
        sa.Column("patient_id", sa.String(length=50), nullable=False),
        sa.Column("interview_id", sa.String(length=50), nullable=True),
        sa.Column("verification_status", sa.String(length=50), server_default="AI-assisted / unverified", nullable=False),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.interview_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_summary_verifications_id"), "summary_verifications", ["id"], unique=False)
    op.create_index(op.f("ix_summary_verifications_verification_id"), "summary_verifications", ["verification_id"], unique=True)
    op.create_index(op.f("ix_summary_verifications_patient_id"), "summary_verifications", ["patient_id"], unique=False)
    op.create_index(op.f("ix_summary_verifications_interview_id"), "summary_verifications", ["interview_id"], unique=False)

    # 2. Doctor Edit Audits Table
    op.create_table(
        "doctor_edit_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("audit_id", sa.String(length=50), nullable=False),
        sa.Column("patient_id", sa.String(length=50), nullable=False),
        sa.Column("interview_id", sa.String(length=50), nullable=True),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("original_value", sa.Text(), nullable=True),
        sa.Column("corrected_value", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.String(length=100), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.interview_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_doctor_edit_audits_id"), "doctor_edit_audits", ["id"], unique=False)
    op.create_index(op.f("ix_doctor_edit_audits_audit_id"), "doctor_edit_audits", ["audit_id"], unique=True)
    op.create_index(op.f("ix_doctor_edit_audits_patient_id"), "doctor_edit_audits", ["patient_id"], unique=False)
    op.create_index(op.f("ix_doctor_edit_audits_interview_id"), "doctor_edit_audits", ["interview_id"], unique=False)
    op.create_index(op.f("ix_doctor_edit_audits_field_name"), "doctor_edit_audits", ["field_name"], unique=False)


def downgrade() -> None:
    op.drop_table("doctor_edit_audits")
    op.drop_table("summary_verifications")
