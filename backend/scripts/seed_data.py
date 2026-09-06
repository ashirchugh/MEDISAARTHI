#!/usr/bin/env python3
"""
Seed script to populate the Medisaarthi PostgreSQL database with synthetic demo patients,
clinical facts, medications, allergies, and timeline events.
"""
import sys
import os
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.orm import Session
from sqlalchemy import select, text
from backend.app.db.database import SessionLocal, engine
from backend.app.models.patient import Patient
from backend.app.models.clinical_fact import ClinicalFact
from backend.app.models.medication import Medication
from backend.app.models.allergy import Allergy
from backend.app.models.timeline_event import TimelineEvent
from backend.app.models.interview import Interview
from backend.app.models.interview_message import InterviewMessage

SYNTHETIC_PATIENTS = [
    {
        "patient_id": "P1001",
        "name": "Rajesh Kumar",
        "age": 48,
        "gender": "male",
        "preferred_language": "hi",
        "phone": "+91 98765 43210",
        "uhid": "APX-2026-0891",
        "registration_time": "09:15 AM",
        "complaint": "Chest pain",
        "duration": "3 days",
        "severity": "7/10",
        "priority": "Priority",
        "status": "Ready for review",
        "conditions": [
            {"condition": "Essential Hypertension", "year": "2021"},
            {"condition": "Type 2 Diabetes Mellitus", "year": "2023"},
        ],
        "medications": [
            {"name": "Amlodipine", "dosage": "5 mg", "frequency": "Once daily (Morning)"},
            {"name": "Metformin", "dosage": "500 mg", "frequency": "Twice daily (After meals)"},
        ],
        "allergies": [
            {"allergen": "No known drug allergies", "reaction": None}
        ],
        "timeline": [
            {"date": "March 2021", "fact": "Hypertension diagnosed during routine health checkup", "source": "EMR", "confidence": 0.98},
            {"date": "July 2023", "fact": "Type 2 Diabetes diagnosed; started on Metformin 500mg", "source": "Clinical Record", "confidence": 0.96},
            {"date": "September 2026 (Today)", "fact": "Current complaint: Onset of central chest tightness with breathlessness × 3 days", "source": "Patient Interview", "confidence": 0.94},
        ],
        "initial_interview": {
            "interview_id": "INT001",
            "messages": [
                {"role": "assistant", "text": "नमस्ते राजेश जी। मेदिमार्थी (Medisaarthi) में आपका स्वागत है। आपको किस वजह से आज अस्पताल आना पड़ा?", "timestamp": "09:18 AM"},
                {"role": "patient", "text": "मुझे तीन दिन से सीने में दर्द हो रहा है और भारीपन लगता है।", "timestamp": "09:19 AM"},
                {"role": "assistant", "text": "समझ गया। दर्द कितना तीव्र (severe) है? अगर 1 से 10 के पैमाने पर बताएं तो कितना होगा?", "timestamp": "09:19 AM"},
                {"role": "patient", "text": "लगभग 7 आउट ऑफ 10. चलने पर बढ़ जाता है।", "timestamp": "09:20 AM"},
                {"role": "assistant", "text": "क्या आपको इसके साथ सांस लेने में दिक्कत या पसीना आ रहा है?", "timestamp": "09:20 AM"},
                {"role": "patient", "text": "हाँ, सांस लेने में थोड़ी तकलीफ होती है और हल्का पसीना भी आता है।", "timestamp": "09:21 AM"},
            ]
        }
    },
    {
        "patient_id": "P1002",
        "name": "Anita Sharma",
        "age": 36,
        "gender": "female",
        "preferred_language": "hi",
        "phone": "+91 98123 45678",
        "uhid": "APX-2026-0892",
        "registration_time": "09:30 AM",
        "complaint": "Fever with chills",
        "duration": "4 days",
        "severity": "6/10",
        "priority": "Normal",
        "status": "Completed",
        "conditions": [],
        "medications": [
            {"name": "Paracetamol", "dosage": "650 mg", "frequency": "SOS for fever > 100°F"},
        ],
        "allergies": [
            {"allergen": "Penicillin", "reaction": "Cutaneous urticaria / skin rash"}
        ],
        "timeline": [
            {"date": "September 2026 (4 days ago)", "fact": "Onset of pyrexia with chills and generalized body ache", "source": "Patient Interview", "confidence": 0.95},
        ]
    },
    {
        "patient_id": "P1003",
        "name": "Rahul Singh",
        "age": 52,
        "gender": "male",
        "preferred_language": "en",
        "phone": "+91 97654 32109",
        "uhid": "APX-2026-0895",
        "registration_time": "09:45 AM",
        "complaint": "Severe throbbing headache",
        "duration": "2 days",
        "severity": "8/10",
        "priority": "Priority",
        "status": "Ready for review",
        "conditions": [
            {"condition": "Chronic Migraine with Visual Aura", "year": "2018"},
        ],
        "medications": [
            {"name": "Sumatriptan", "dosage": "50 mg", "frequency": "At onset of migraine attack"},
            {"name": "Naproxen", "dosage": "250 mg", "frequency": "PRN for pain relief"},
        ],
        "allergies": [
            {"allergen": "No known drug allergies", "reaction": None}
        ],
        "timeline": [
            {"date": "June 2018", "fact": "Migraine with visual aura diagnosed by neurologist", "source": "EMR", "confidence": 0.97},
            {"date": "September 2026 (Today)", "fact": "Acute severe unilateral pulsating headache with photophobia × 2 days", "source": "Patient Interview", "confidence": 0.95},
        ]
    },
    {
        "patient_id": "P1004",
        "name": "Priya Verma",
        "age": 29,
        "gender": "female",
        "preferred_language": "hi",
        "phone": "+91 99887 76655",
        "uhid": "APX-2026-0901",
        "registration_time": "10:05 AM",
        "complaint": "Acute Right Lower Abdominal Pain",
        "duration": "24 hours",
        "severity": "8/10",
        "priority": "Urgent",
        "status": "Ready for review",
        "conditions": [
            {"condition": "Hypothyroidism", "year": "2022"},
        ],
        "medications": [
            {"name": "Levothyroxine", "dosage": "50 mcg", "frequency": "Daily (Empty stomach morning)"},
        ],
        "allergies": [
            {"allergen": "Sulfa drugs", "reaction": "Cutaneous maculopapular rash"}
        ],
        "timeline": [
            {"date": "November 2022", "fact": "Primary hypothyroidism diagnosed; started on Levothyroxine", "source": "Clinical Record", "confidence": 0.96},
            {"date": "September 2026 (Today)", "fact": "Acute right lower quadrant abdominal pain onset 24h ago with nausea", "source": "Patient Interview", "confidence": 0.94},
        ]
    },
    {
        "patient_id": "P1005",
        "name": "Amit Gupta",
        "age": 61,
        "gender": "male",
        "preferred_language": "en",
        "phone": "+91 91234 56780",
        "uhid": "APX-2026-0914",
        "registration_time": "10:20 AM",
        "complaint": "Chronic Lower Back Pain flare",
        "duration": "2 weeks",
        "severity": "6/10",
        "priority": "Normal",
        "status": "Verified",
        "conditions": [
            {"condition": "Lumbar Spondylosis (L4-L5)", "year": "2019"},
            {"condition": "Dyslipidemia", "year": "2020"},
        ],
        "medications": [
            {"name": "Atorvastatin", "dosage": "20 mg", "frequency": "Nightly for lipid control"},
            {"name": "Aceclofenac", "dosage": "100 mg", "frequency": "PRN after meals"},
        ],
        "allergies": [
            {"allergen": "No known drug allergies", "reaction": None}
        ],
        "timeline": [
            {"date": "January 2019", "fact": "Lumbar spondylosis diagnosed on MRI lumbar spine", "source": "EMR", "confidence": 0.98},
            {"date": "August 2020", "fact": "Dyslipidemia diagnosed; started on Atorvastatin 20mg", "source": "Clinical Record", "confidence": 0.97},
            {"date": "September 2026 (Today)", "fact": "2-week flare of mechanical lower back pain radiating to left leg", "source": "Patient Interview", "confidence": 0.95},
        ]
    }
]


def seed_database(db: Session):
    print("🌱 Seeding Medisaarthi database with synthetic patient records...")

    for pdata in SYNTHETIC_PATIENTS:
        # Check if patient exists
        stmt = select(Patient).where(Patient.patient_id == pdata["patient_id"])
        existing = db.scalars(stmt).first()

        if existing:
            print(f"  • Patient {pdata['patient_id']} ({pdata['name']}) already exists. Updating details...")
            patient = existing
            patient.name = pdata["name"]
            patient.age = pdata["age"]
            patient.gender = pdata["gender"]
            patient.preferred_language = pdata["preferred_language"]
            patient.phone = pdata.get("phone")
            patient.uhid = pdata.get("uhid")
            patient.registration_time = pdata.get("registration_time")
        else:
            patient = Patient(
                patient_id=pdata["patient_id"],
                name=pdata["name"],
                age=pdata["age"],
                gender=pdata["gender"],
                preferred_language=pdata["preferred_language"],
                phone=pdata.get("phone"),
                uhid=pdata.get("uhid"),
                registration_time=pdata.get("registration_time"),
            )
            db.add(patient)
            db.flush()
            print(f"  + Created patient {patient.patient_id}: {patient.name}")

        # Clear existing child records to maintain clean idempotency
        db.query(ClinicalFact).filter(ClinicalFact.patient_id == patient.patient_id).delete()
        db.query(Medication).filter(Medication.patient_id == patient.patient_id).delete()
        db.query(Allergy).filter(Allergy.patient_id == patient.patient_id).delete()
        db.query(TimelineEvent).filter(TimelineEvent.patient_id == patient.patient_id).delete()

        # Seed Clinical Facts
        facts_to_add = [
            ClinicalFact(patient_id=patient.patient_id, field_name="chief_complaint", value=pdata["complaint"], source="current_interview", confidence=0.95, status="confirmed"),
            ClinicalFact(patient_id=patient.patient_id, field_name="duration", value=pdata["duration"], source="current_interview", confidence=0.95, status="confirmed"),
            ClinicalFact(patient_id=patient.patient_id, field_name="severity", value=pdata["severity"], source="current_interview", confidence=0.95, status="confirmed"),
            ClinicalFact(patient_id=patient.patient_id, field_name="priority", value=pdata["priority"], source="current_interview", confidence=1.0, status="confirmed"),
            ClinicalFact(patient_id=patient.patient_id, field_name="status", value=pdata["status"], source="current_interview", confidence=1.0, status="confirmed"),
        ]
        for c in pdata.get("conditions", []):
            facts_to_add.append(
                ClinicalFact(patient_id=patient.patient_id, field_name="condition", value=f"{c['condition']} ({c['year']})", source="patient_history", confidence=0.98, status="confirmed")
            )
        db.add_all(facts_to_add)

        # Seed Medications
        for m in pdata.get("medications", []):
            db.add(Medication(patient_id=patient.patient_id, name=m["name"], dosage=m["dosage"], frequency=m.get("frequency"), source="patient_history"))

        # Seed Allergies
        for a in pdata.get("allergies", []):
            db.add(Allergy(patient_id=patient.patient_id, allergen=a["allergen"], reaction=a.get("reaction"), source="patient_history"))

        # Seed Timeline Events
        for t in pdata.get("timeline", []):
            db.add(TimelineEvent(patient_id=patient.patient_id, date=t["date"], fact=t["fact"], source=t.get("source", "previous_consultation"), confidence=t.get("confidence", 0.95)))

        # Seed Initial Interview if provided (e.g. for Rajesh Kumar P1001)
        if "initial_interview" in pdata:
            i_data = pdata["initial_interview"]
            db.query(InterviewMessage).filter(InterviewMessage.interview_id == i_data["interview_id"]).delete()
            db.query(Interview).filter(Interview.interview_id == i_data["interview_id"]).delete()

            interview = Interview(
                interview_id=i_data["interview_id"],
                patient_id=patient.patient_id,
                status="active",
                language=patient.preferred_language,
                current_topic="chief_complaint",
                started_at=datetime.utcnow(),
            )
            db.add(interview)
            db.flush()

            for msg in i_data.get("messages", []):
                db.add(
                    InterviewMessage(
                        interview_id=interview.interview_id,
                        role=msg["role"],
                        text=msg["text"],
                        language=patient.preferred_language,
                        timestamp=datetime.utcnow(),
                    )
                )

    db.commit()
    print("✅ Database successfully seeded with 5 synthetic patient records!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
