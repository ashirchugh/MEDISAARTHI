from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class ClinicalFact(Base):
    __tablename__ = "clinical_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interview_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("interviews.interview_id", ondelete="SET NULL"), nullable=True, index=True
    )
    patient_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., 'chief_complaint', 'duration', 'severity', 'associated_symptom', 'condition'
    value: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="current_interview"
    )  # 'current_interview', 'previous_consultation', 'patient_history', 'doctor_verified'
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="confirmed"
    )  # 'confirmed', 'uncertain', 'unknown', 'conflict'

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="clinical_facts")
    interview: Mapped[Optional["Interview"]] = relationship("Interview", back_populates="clinical_facts")
