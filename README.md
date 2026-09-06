# Medisaarthi — AI-Powered Pre-Consultation Intelligence Platform

> **Clinical Workflow Positioning**: Sits seamlessly between **Patient Registration** and **Doctor Consultation** in hospital OPD workflows. Conducts guided multilingual pre-consultation interviews with structured symptom intake and presents physician-verified clinical intelligence to attending doctors.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🏥 Product Routes & Architecture

| Route | Purpose | Key Capabilities |
|---|---|---|
| `/` | **Landing Portal** | Overview, dual portal launcher, demo story breakdown |
| `/patient` | **Patient Welcome** | High-contrast welcome screen, privacy reassurance, start CTA |
| `/patient/language` | **Language Selection** | Large, accessible cards for Hindi (🇮🇳 हिंदी) & English (🇬🇧) |
| `/patient/consent` | **Patient Consent** | Simple explanation, interactive agreement, "Why do we ask this?" FAQ |
| `/patient/identify` | **Patient Identification** | Registration ID input, one-click demo patient switcher, live verification card |
| `/patient/interview` | **AI Consultation Assistant** | Conversational consultation, voice recording with animated waveform, live structured data panel, quick suggestion chips |
| `/patient/completed` | **Interview Completion** | Extracted summary review, trust confirmation, hand-off to doctor portal |
| `/doctor/login` | **Doctor Login** | Clinical access portal, one-click demo physician login |
| `/doctor` | **Doctor Dashboard** | KPI overview, search by symptom/name, status and priority filters, patient queue |
| `/doctor/patients/[id]` | **Patient Clinical Profile** | Chief complaint, priority review flags, AI summary, longitudinal timeline, history, medications, allergies, transcript drawer, edit & approve modal |

---

## 👥 Demo Patient Profiles

The application comes pre-loaded with realistic synthetic patient profiles:

| Patient ID | Name | Age / Gender | Chief Complaint | Key History & Medications | Priority Level |
|---|---|---|---|---|---|
| `P1001` | **Rajesh Kumar** | 48 M | Chest pain × 3 days (Sev: 7/10) with breathlessness | HTN (2021, Amlodipine 5mg), Diabetes (2023, Metformin 500mg), NKDA | ⚡ Priority Review |
| `P1002` | **Anita Sharma** | 36 F | Fever with chills × 4 days (Sev: 6/10) | Paracetamol 650mg, Allergy: Penicillin | Normal |
| `P1003` | **Rahul Singh** | 52 M | Throbbing Headache × 2 days (Sev: 8/10) with visual aura | Migraine (2018), Sumatriptan 50mg, Naproxen, NKDA | ⚡ Priority Review |
| `P1004` | **Priya Verma** | 29 F | Right Lower Abdominal Pain × 24h (Sev: 8/10) | Hypothyroidism (2022, Levothyroxine 50mcg), Allergy: Sulfa drugs | 🚨 Urgent Review |
| `P1005` | **Amit Gupta** | 61 M | Lumbar Back Pain flare × 2 weeks (Sev: 6/10) | Lumbar Spondylosis (2019), Dyslipidemia (Atorvastatin 20mg) | Normal (Verified) |

---

## 🎬 End-to-End Demo Script

To execute the demo required by the specification:

1. Open **[http://localhost:3000](http://localhost:3000)** and click **"Launch Patient Experience"**.
2. On the Welcome screen, click **"Start"**.
3. Select **"हिंदी (Hindi)"** and click **"आगे बढ़ें"**.
4. Check the consent box (**"मैं समझता/समझती हूँ और सहमत हूँ"**) and continue.
5. Select **"P1001 Rajesh Kumar"** and click **"इंटरव्यू शुरू करें"**.
6. The AI asks: `"नमस्ते राजेश जी... आपको किस वजह से आज अस्पताल आना पड़ा?"`
7. Click the **Voice Microphone** or tap the quick chip: `"मुझे तीन दिन से सीने में दर्द हो रहा है..."`.
8. Watch the structured panel dynamically extract:
   - **Chief Complaint:** Chest pain
   - **Duration:** 3 days
9. Answer the follow-up questions for **Severity (7/10)**, **Breathlessness / Sweating**, and **BP/Sugar medications**.
10. Click **"View Summary"** on completion, then click **"View in Doctor Dashboard"**.
11. In the Doctor Dashboard, open **#P1001 Rajesh Kumar**.
12. Review the **Priority Attention Banner**, **AI Interview Summary**, **Timeline**, **Medications (Amlodipine, Metformin)**, and **NKDA**.
13. Click **"View Full Interview"** to inspect the transcript.
14. Click **"Edit Summary"**, adjust clinical notes or symptoms, and click **"Save Changes"**.
15. Click **"Approve & Verify"** — status transitions to **Verified by Physician** with an instant confirmation toast.

---

## 🔌 Connecting to Real Backend APIs

The frontend features a clean abstraction layer in `src/services/api.ts` and `src/lib/api/index.ts`. To connect to a live FastAPI + PostgreSQL + LLM backend:

1. Set `NEXT_PUBLIC_API_URL=https://api.medisaarthi.hospital.org` in your environment.
2. Replace mock implementations in `src/services/api.ts`:
   - `getPatients()` $\rightarrow$ `GET /api/v1/doctor/patients`
   - `getClinicalSummary(id)` $\rightarrow$ `GET /api/v1/doctor/patients/{id}/summary`
   - `startInterview(id)` $\rightarrow$ `POST /api/v1/interview/start`
   - `sendInterviewResponse(...)` $\rightarrow$ `POST /api/v1/interview/respond`
   - `completeInterview(...)` $\rightarrow$ `POST /api/v1/interview/complete`
   - `approveSummary(id, notes)` $\rightarrow$ `POST /api/v1/doctor/patients/{id}/verify`
   - `updatePatientSummary(id, data)` $\rightarrow$ `PATCH /api/v1/doctor/patients/{id}/summary`

No changes to UI components will be required.

---

## 📂 Project Structure

```
src/
├── app/
│   ├── layout.tsx                # Global HTML metadata & root styling
│   ├── page.tsx                  # Landing portal & dual experience launcher
│   ├── globals.css               # Medical design tokens, animations & waveforms
│   ├── patient/
│   │   ├── layout.tsx            # Patient container layout
│   │   ├── page.tsx              # Screen 1: Welcome screen
│   │   ├── language/page.tsx     # Screen 2: Language selector
│   │   ├── consent/page.tsx      # Screen 3: Patient consent & FAQ
│   │   ├── identify/page.tsx     # Screen 4: Patient identification & demo switcher
│   │   ├── interview/page.tsx    # Screen 5: Conversational AI interview & voice UI
│   │   └── completed/page.tsx    # Screen 6: Intake summary & completion
│   └── doctor/
│       ├── layout.tsx            # Doctor dashboard layout & sidebar
│       ├── login/page.tsx        # Clinical staff login
│       ├── page.tsx              # Doctor dashboard, queue & search
│       └── patients/
│           └── [id]/page.tsx     # Physician patient chart & verification
├── components/
│   ├── ui/                       # Reusable Button, Card, Badge, Modal, Drawer
│   ├── patient/                  # PatientHeader, VoiceRecorder, ChatMessage, ExtractedInfo, etc.
│   └── doctor/                   # DashboardHeader, PatientList, Timeline, Cards, Drawer, Modals
├── lib/
│   ├── mock-data.ts              # Synthetic patient datasets & histories
│   ├── interview-engine.ts       # Conversational question flow & symptom extraction
│   └── api/index.ts              # Unified API export
├── services/
│   └── api.ts                    # Centralized mock API with local persistence
└── types/
    └── index.ts                  # Centralized TypeScript clinical data contracts
```

---

## 🛡️ Medical Safety & UX Guardrails

- **AI is Pre-Consultation Only**: Medisaarthi explicitly labels all AI-generated content with `"AI-generated • Requires physician verification"`.
- **No Unsupervised Autonomous Diagnoses**: The attending doctor retains final authority to edit, verify, and approve patient data before entering consultation.
- **Accessible Design**: Touch targets adhere to $\ge 48\text{px}$ minimums for elderly and mobile users.
