from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class DoctorEditAudit(Base):
    __tablename__ = "doctor_edit_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    patient_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True
    )
    interview_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("interviews.interview_id", ondelete="SET NULL"), nullable=True, index=True
    )
    field_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # e.g., 'chief_complaint', 'severity', 'location', 'trigger', 'associated_symptoms', 'medications', 'allergies', 'past_medical_history'
    original_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str] = mapped_column(String(100), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="edit_audits")
    interview: Mapped[Optional["Interview"]] = relationship("Interview", back_populates="edit_audits")
