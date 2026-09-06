from datetime import datetime
from sqlalchemy import String, Integer, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "March 2021" or "2021-05-12"
    fact: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="previous_consultation"
    )  # 'EMR', 'Patient Interview', 'Clinical Record', 'previous_consultation'
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="timeline_events")
