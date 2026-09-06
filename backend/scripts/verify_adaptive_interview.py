"""Live End-to-End Adaptive Interview Verification Script for Medisaarthi.

Demonstrates conditional question graph branching in live multi-turn dialogues:
1. Fever + Respiratory Pathway
2. Fever + GI Pathway
3. Fever Standard Non-Branching Pathway
"""
import httpx
from sqlalchemy import select
from backend.app.db.database import SessionLocal
from backend.app.models.interview import Interview
from backend.app.models.clinical_fact import ClinicalFact

BASE_URL = "http://localhost:8000"


def run_adaptive_demo(title: str, patient_id: str, turns: list):
    print(f"\n========================================================")
    print(f"ADAPTIVE DEMO: {title} (Patient: {patient_id})")
    print(f"========================================================")

    # 1. Start interview
    r_start = httpx.post(f"{BASE_URL}/interview/start", json={"patient_id": patient_id, "language": "hi"}, timeout=25.0)
    start_data = r_start.json()
    int_id = start_data["interview_id"]
    print(f"Assistant: {start_data['initial_question']['text']}\n")

    for i, msg in enumerate(turns, 1):
        print(f"Patient: '{msg}'")
        r = httpx.post(f"{BASE_URL}/interview/respond", json={"interview_id": int_id, "message": msg}, timeout=25.0)
        data = r.json()
        print(f"Assistant: '{data['next_question']['text']}'")
        print(f"Next Topic: {data['current_topic']} | Completed: {data['interview_completed']}")
        print(f"Extracted Facts: {[f['field_name'] + '=' + f['value'] for f in data['extracted_facts']]}\n")
        if data["interview_completed"]:
            break

    db = SessionLocal()
    try:
        facts = db.scalars(select(ClinicalFact).where(ClinicalFact.interview_id == int_id)).all()
        print(f"Stored PostgreSQL Facts ({len(facts)}): {[f.field_name + ': ' + f.value for f in facts]}")
    finally:
        db.close()


def main():
    # 1. Fever + Respiratory Pathway
    run_adaptive_demo(
        title="Fever + Respiratory Pathway (Cough present -> Sputum/Breathlessness follow-up)",
        patient_id="P1002",
        turns=[
            "Mujhe 2 din se bukhar hai, sath mein khansi aur gale mein dard hai.",
            "Temperature 101 degree tha, thand lag rahi hai.",
            "Sukhi khansi hai, balgam nahi hai aur saans lene mein takleef nahi hai.",
        ],
    )

    # 2. Fever + GI Pathway
    run_adaptive_demo(
        title="Fever + GI Pathway (No cough, Vomiting & Stomach pain -> Bowel symptoms follow-up)",
        patient_id="P1002",
        turns=[
            "Mujhe 2 din se bukhar hai, khansi nahi hai par ulti aur pet mein dard hai.",
            "Temperature 102 degree tha, thand lagti hai.",
            "Dast nahi hue, pet thoda kharab hai.",
        ],
    )


if __name__ == "__main__":
    main()
