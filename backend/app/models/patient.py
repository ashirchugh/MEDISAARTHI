from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)  # 'male', 'female', 'other'
    preferred_language: Mapped[str] = mapped_column(String(10), nullable=False, default="hi")  # 'hi', 'en'
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    uhid: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    registration_time: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    interviews: Mapped[List["Interview"]] = relationship(
        "Interview", back_populates="patient", cascade="all, delete-orphan"
    )
    medications: Mapped[List["Medication"]] = relationship(
        "Medication", back_populates="patient", cascade="all, delete-orphan"
    )
    allergies: Mapped[List["Allergy"]] = relationship(
        "Allergy", back_populates="patient", cascade="all, delete-orphan"
    )
    timeline_events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent", back_populates="patient", cascade="all, delete-orphan"
    )
    clinical_facts: Mapped[List["ClinicalFact"]] = relationship(
        "ClinicalFact", back_populates="patient", cascade="all, delete-orphan"
    )
    verifications: Mapped[List["SummaryVerification"]] = relationship(
        "SummaryVerification", back_populates="patient", cascade="all, delete-orphan"
    )
    edit_audits: Mapped[List["DoctorEditAudit"]] = relationship(
        "DoctorEditAudit", back_populates="patient", cascade="all, delete-orphan"
    )
