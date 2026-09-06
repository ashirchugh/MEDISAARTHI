from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interview_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # 'active', 'completed', 'cancelled'
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="hi")
    current_topic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="interviews")
    messages: Mapped[List["InterviewMessage"]] = relationship(
        "InterviewMessage", back_populates="interview", cascade="all, delete-orphan", order_by="InterviewMessage.timestamp"
    )
    clinical_facts: Mapped[List["ClinicalFact"]] = relationship(
        "ClinicalFact", back_populates="interview"
    )
    verifications: Mapped[List["SummaryVerification"]] = relationship(
        "SummaryVerification", back_populates="interview"
    )
    edit_audits: Mapped[List["DoctorEditAudit"]] = relationship(
        "DoctorEditAudit", back_populates="interview"
    )
