# Medisaarthi Backend — Foundation Architecture (Step 1)

Medisaarthi is an AI-powered pre-consultation intelligence platform for hospitals. This backend provides the core data persistence layer, clinical models, RESTful APIs, and migration management bridging patient registration and doctor consultation.

---

## 🏛️ System Architecture

```
Frontend (Next.js / TypeScript @ :3000)
             │
             ▼  [REST API / JSON]
FastAPI Application Layer (backend/app/main.py @ :8000)
             │
             ▼
Service & Business Logic Layer (backend/app/services/)
   ├── patient_service.py
   ├── interview_service.py
   └── doctor_service.py
             │
             ▼  [SQLAlchemy 2.0 ORM + Pydantic v2 Validation]
PostgreSQL Database Layer (Database: `medisaarthi` @ :5432)
   ├── patients
   ├── interviews
   ├── interview_messages
   ├── clinical_facts
   ├── medications
   ├── allergies
   └── timeline_events
```

---

## 🧩 Architectural Component Roles

| Component | Technology | Responsibility |
|---|---|---|
| **API Framework** | **FastAPI** | High-performance asynchronous REST API routing, dependency injection, CORS middleware, and automatic OpenAPI / Swagger interactive documentation (`/docs`). |
| **Database Engine** | **PostgreSQL** | Relational data persistence with strict foreign key constraints, indexing on `patient_id` and `interview_id`, and cascade deletion rules. |
| **Object-Relational Mapper** | **SQLAlchemy 2.0** | Type-safe declarative database models (`Mapped`, `mapped_column`) with explicit relational mappings separating database queries from route handlers. |
| **Schema & Validation** | **Pydantic v2** | Strict input/output request and response validation, serializing clinical structures, and preventing exposure of raw internal database models. |
| **Schema Migrations** | **Alembic** | Version-controlled, reproducible database schema migrations (`upgrade head` / `downgrade`) ensuring reproducible environments. |

---

## 💾 Core Database Entities

1. **`patients`**: Master demographic profiles with human-facing `patient_id` (e.g., `P1001`), age, gender, preferred language (`hi`/`en`), UHID, and registration metadata.
2. **`interviews`**: Pre-consultation interview sessions tracked by `interview_id` (e.g., `INT001`), linked to patient, with status (`active`, `completed`, `cancelled`).
3. **`interview_messages`**: Granular, chronological conversation history capturing every message from `system`, `assistant`, and `patient`.
4. **`clinical_facts`**: Normalized structured symptom extractions (e.g., `chief_complaint`, `duration`, `severity`, `priority`) with source tracking and confidence scores.
5. **`medications`**: Active regular prescriptions (drug name, dosage, frequency, source).
6. **`allergies`**: Known drug and substance hypersensitivities (allergen, reaction, source).
7. **`timeline_events`**: Longitudinal medical milestones (dates, verified facts, source, confidence).

---

## 🔌 API Endpoints (Step 1 & Step 2A)

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/health` | Live PostgreSQL connectivity & health check | `200 OK` / `503` |
| `GET` | `/patients/{patient_id}` | Retrieve patient demographic record (e.g. `P1001`) | `200 OK` / `404` |
| `GET` | `/patients/{patient_id}/history` | Retrieve structured conditions, medications, allergies, timeline | `200 OK` / `404` |
| `POST` | `/interview/start` | Initialize pre-consultation session & receive initial intake question | `201 Created` |
| `POST` | `/interview/respond` | **(Step 2A)** Submit patient reply, extract facts, persist state, and get next question | `200 OK` / `400` / `404` |
| `GET` | `/doctor/patients` | Retrieve doctor's patient triage queue with complaints & status | `200 OK` |
| `GET` | `/docs` | Interactive Swagger UI API documentation | `200 OK` |

---

## 🤖 Step 2B: Gemini Language Understanding & AIProvider Architecture

In **Step 2B**, Medisaarthi integrates **Google Gemini** as an intelligent language understanding and conversational rephrasing layer via the official `google-genai` SDK, while preserving deterministic question control in the **Question Graph**.

```
Patient Response
       │
       ▼
[FastAPI /interview/respond]
       │
       ▼
[Interview Engine] ──────────────────────────┐
       │                                     ▼
       ├─────────────────────────► [AIProvider (Gemini / Mock)]
       │                                     │
       │                                     ├─► Structured Extraction (JSON Schema)
       │                                     └─► Conversational Question Phrasing
       ▼                                     │ (Fallback on timeout/error)
[Question Graph State Machine] ◄─────────────┘
  (Controls Required Topics,
   Missing Topics, & Completion)
       │
       ▼
[PostgreSQL clinical_facts & interview_messages]
```

### 1. Architectural Principles
- **Separation of Control**: The LLM *never* decides which clinical topics are required or when an interview completes. The **Question Graph** remains the deterministic authority.
- **Provider Abstraction (`backend/app/services/ai/`)**:
  - `base.py`: Abstract `AIProvider` defining `extract_facts`, `generate_question`, and `generate_summary`.
  - `mock_provider.py`: Fast, deterministic offline provider for development and automated testing without external API calls.
  - `gemini_provider.py`: Production integration utilizing `google-genai` with strict Pydantic JSON schemas, safety system prompts, and latency logging.
  - `schemas.py`: Pydantic validation models (`LLMExtractedFact`, `LLMExtractedFactsResult`, `LLMQuestionResult`).
- **Resilient Fallback Hierarchy**:
  ```
  Gemini API Call
       │ (Timeout / Rate Limit / Parse Failure / No Key)
       ▼
  Deterministic Rule Extractor (`fact_extractor.py`)
       │
       ▼
  Bilingual Question Templates (`question_graph.py`)
  ```

### 2. Configuration & Environment Variables

| Variable | Description | Default | Allowed Values |
|---|---|---|---|
| `AI_PROVIDER` | Active AI provider mode | `mock` | `mock`, `gemini` |
| `GEMINI_API_KEY` | Google Gemini API Key | *(empty)* | Secret key string |
| `GEMINI_MODEL` | Gemini LLM model | `gemini-2.5-flash` | `gemini-2.5-flash`, `gemini-2.0-flash` |

> [!WARNING]
> **Security Notice**: Never commit `GEMINI_API_KEY` to git or expose it in frontend bundles. The key is accessed strictly backend-side by FastAPI.

### 3. Running with Mock Provider (Default / Testing)
```bash
# In backend/.env
AI_PROVIDER=mock

# Run tests
PYTHONPATH=. ./backend/venv/bin/pytest backend/tests -v
```

### 4. Running with Real Gemini API
```bash
# In backend/.env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Start server
PYTHONPATH=. uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```


---

## 🛠️ Local Setup Guide

### 1. Prerequisites
- Python 3.9+ (Python 3.10+ recommended)
- PostgreSQL 14+ or Docker

---

### 2. Database Setup

#### Option A: Local PostgreSQL
```bash
# Connect to PostgreSQL and create the database
psql -U postgres -c "CREATE DATABASE medisaarthi;"
```

#### Option B: Docker Compose (One-Click PostgreSQL)
```bash
# Start PostgreSQL container in background
docker compose -f backend/docker-compose.yml up -d
```

---

### 3. Python Virtual Environment Setup

```bash
# Navigate to repository root
cd /path/to/MEDISAARTHI

# Create virtual environment
python3 -m venv backend/venv

# Activate virtual environment
source backend/venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
```

---

### 4. Configure Environment Variables

```bash
# Copy example environment configuration
cp backend/.env.example backend/.env

# Update DATABASE_URL in backend/.env if your Postgres credentials differ:
# DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/medisaarthi
```

---

### 5. Run Database Migrations

```bash
# Run Alembic migrations to create tables
PYTHONPATH=. alembic -c backend/alembic.ini upgrade head
```

---

### 6. Populate Synthetic Demo Patients

```bash
# Run idempotent seed script
PYTHONPATH=. python3 backend/scripts/seed_data.py
```

This seeds 5 synthetic patient profiles:
- `P1001`: **Rajesh Kumar** (48M, Chest pain × 3 days, HTN, T2DM, Amlodipine, Metformin)
- `P1002`: **Anita Sharma** (36F, Fever with chills × 4 days, Penicillin allergy)
- `P1003`: **Rahul Singh** (52M, Throbbing headache × 2 days, Migraine history)
- `P1004`: **Priya Verma** (29F, Acute lower right abdominal pain × 24h, Sulfa allergy)
- `P1005`: **Amit Gupta** (61M, Lower back pain flare × 2 weeks, Lumbar spondylosis)

---

### 7. Start FastAPI Application

```bash
# Start uvicorn server on port 8000
PYTHONPATH=. uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 8. Access Interactive API Documentation

Open your browser at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### 9. Run Automated Test Suite

```bash
# Run all unit and integration tests with pytest
PYTHONPATH=. ./backend/venv/bin/pytest backend/tests -v
```

---

## 🔗 How Frontend Connects to Backend

In future steps, the frontend's mock service in `src/services/api.ts` can be switched from browser local storage to HTTP fetch calls against `http://localhost:8000`:

```typescript
// Example: src/services/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function getPatient(patientId: string): Promise<Patient | null> {
  const res = await fetch(`${API_BASE}/patients/${patientId}`);
  if (!res.ok) return null;
  return res.json();
}

export async function startInterview(patientId: string, language: string = 'hi') {
  const res = await fetch(`${API_BASE}/interview/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patient_id: patientId, language }),
  });
  return res.json();
}
```
