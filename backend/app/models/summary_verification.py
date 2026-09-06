from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class SummaryVerification(Base):
    __tablename__ = "summary_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verification_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    patient_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True
    )
    interview_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("interviews.interview_id", ondelete="SET NULL"), nullable=True, index=True
    )
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="AI-assisted / unverified"
    )  # 'AI-assisted / unverified', 'Verified'
    verified_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="verifications")
    interview: Mapped[Optional["Interview"]] = relationship("Interview", back_populates="verifications")
