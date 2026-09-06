"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-06 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Patients Table
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=False),
        sa.Column("preferred_language", sa.String(length=10), server_default="hi", nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("uhid", sa.String(length=50), nullable=True),
        sa.Column("registration_time", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_id"),
    )
    op.create_index(op.f("ix_patients_patient_id"), "patients", ["patient_id"], unique=True)

    # 2. Interviews Table
    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("interview_id", sa.String(length=50), nullable=False),
        sa.Column("patient_id", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("language", sa.String(length=10), server_default="hi", nullable=False),
        sa.Column("current_topic", sa.String(length=100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("interview_id"),
    )
    op.create_index(op.f("ix_interviews_interview_id"), "interviews", ["interview_id"], unique=True)
    op.create_index(op.f("ix_interviews_patient_id"), "interviews", ["patient_id"], unique=False)

    # 3. Interview Messages Table
    op.create_table(
        "interview_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("interview_id", sa.String(length=50), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=10), server_default="hi", nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.interview_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_messages_interview_id"), "interview_messages", ["interview_id"], unique=False)

    # 4. Clinical Facts Table
    op.create_table(
        "clinical_facts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("interview_id", sa.String(length=50), nullable=True),
        sa.Column("patient_id", sa.String(length=50), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=50), server_default="current_interview", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="confirmed", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.interview_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinical_facts_patient_id"), "clinical_facts", ["patient_id"], unique=False)
    op.create_index(op.f("ix_clinical_facts_interview_id"), "clinical_facts", ["interview_id"], unique=False)

    # 5. Medications Table
    op.create_table(
        "medications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("dosage", sa.String(length=100), nullable=False),
        sa.Column("frequency", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=50), server_default="patient_history", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medications_patient_id"), "medications", ["patient_id"], unique=False)

    # 6. Allergies Table
    op.create_table(
        "allergies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.String(length=50), nullable=False),
        sa.Column("allergen", sa.String(length=200), nullable=False),
        sa.Column("reaction", sa.String(length=200), nullable=True),
        sa.Column("source", sa.String(length=50), server_default="patient_history", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_allergies_patient_id"), "allergies", ["patient_id"], unique=False)

    # 7. Timeline Events Table
    op.create_table(
        "timeline_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.String(length=50), nullable=False),
        sa.Column("date", sa.String(length=100), nullable=False),
        sa.Column("fact", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=50), server_default="previous_consultation", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0.95", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_timeline_events_patient_id"), "timeline_events", ["patient_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_timeline_events_patient_id"), table_name="timeline_events")
    op.drop_table("timeline_events")
    op.drop_index(op.f("ix_allergies_patient_id"), table_name="allergies")
    op.drop_table("allergies")
    op.drop_index(op.f("ix_medications_patient_id"), table_name="medications")
    op.drop_table("medications")
    op.drop_index(op.f("ix_clinical_facts_interview_id"), table_name="clinical_facts")
    op.drop_index(op.f("ix_clinical_facts_patient_id"), table_name="clinical_facts")
    op.drop_table("clinical_facts")
    op.drop_index(op.f("ix_interview_messages_interview_id"), table_name="interview_messages")
    op.drop_table("interview_messages")
    op.drop_index(op.f("ix_interviews_patient_id"), table_name="interviews")
    op.drop_index(op.f("ix_interviews_interview_id"), table_name="interviews")
    op.drop_table("interviews")
    op.drop_index(op.f("ix_patients_patient_id"), table_name="patients")
    op.drop_table("patients")
