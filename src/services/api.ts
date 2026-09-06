/**
 * Medisaarthi Frontend API Service Layer
 * Connects frontend directly to FastAPI backend.
 */
import {
  Patient,
  PatientListItem,
  BackendInterviewStartResponse,
  BackendInterviewRespondResponse,
  BackendInterviewVoiceResponse,
  BackendInterviewDetailResponse,
  DoctorSummaryResponse,
  DoctorNarrativeResponse,
  DoctorEditAuditItem,
  DoctorSummaryEditRequest,
  DoctorSummaryEditResponse,
  DoctorSummaryVerifyResponse,
  Language,
} from '@/types';
import { INITIAL_PATIENTS } from '@/lib/mock-data';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorDetail = `Request failed with status ${res.status}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorDetail = typeof errorJson.detail === 'string'
            ? errorJson.detail
            : JSON.stringify(errorJson.detail);
        }
      } catch {
        // use default error message
      }
      throw new ApiError(errorDetail, res.status);
    }

    return await res.json();
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err?.message || 'Unable to connect to Medisaarthi backend server. Please check your connection.',
      0
    );
  }
}

/**
 * Fetch list of all patients registered in PostgreSQL
 */
export async function getPatients(): Promise<Patient[]> {
  try {
    return await request<Patient[]>('/patients');
  } catch {
    return INITIAL_PATIENTS;
  }
}

/**
 * Fetch a single patient by ID from PostgreSQL
 */
export async function getPatient(patientId: string): Promise<Patient | null> {
  try {
    return await request<Patient>(`/patients/${encodeURIComponent(patientId)}`);
  } catch (err: any) {
    if (err?.status === 404) {
      return null;
    }
    const fallback = INITIAL_PATIENTS.find(
      (p) => p.patient_id.toLowerCase() === patientId.trim().toLowerCase()
    );
    return fallback || null;
  }
}

/**
 * Start a pre-consultation interview session on the backend
 * POST /interview/start
 */
export async function startInterviewSession(
  patientId: string,
  language: Language = 'hi'
): Promise<BackendInterviewStartResponse> {
  return await request<BackendInterviewStartResponse>('/interview/start', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: patientId,
      language: language,
    }),
  });
}

/**
 * Send patient response to backend for adaptive question progression & fact extraction
 * POST /interview/respond
 */
export async function respondToInterviewSession(
  interviewId: string,
  message: string
): Promise<BackendInterviewRespondResponse> {
  return await request<BackendInterviewRespondResponse>('/interview/respond', {
    method: 'POST',
    body: JSON.stringify({
      interview_id: interviewId,
      message: message,
    }),
  });
}

/**
 * Send patient audio recording for Speech-to-Text transcription and interview progression
 * POST /interview/{interview_id}/voice
 */
export async function sendVoiceInterviewAudio(
  interviewId: string,
  audioBlob: Blob,
  filename: string = 'recording.webm'
): Promise<BackendInterviewVoiceResponse> {
  const formData = new FormData();
  formData.append('audio', audioBlob, filename);

  const url = `${API_BASE_URL}/interview/${encodeURIComponent(interviewId)}/voice`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      let errorDetail = `Voice request failed with status ${res.status}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorDetail = typeof errorJson.detail === 'string'
            ? errorJson.detail
            : JSON.stringify(errorJson.detail);
        }
      } catch {}
      throw new ApiError(errorDetail, res.status);
    }

    return await res.json();
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err?.message || 'Unable to upload voice recording. Please check connection.',
      0
    );
  }
}

/**
 * Explicitly mark an interview completed on the backend
 * POST /interview/complete
 */
export async function completeInterviewSession(
  interviewId: string
): Promise<{ interview_id: string; status: string; completed_at?: string }> {
  return await request<{ interview_id: string; status: string; completed_at?: string }>(
    '/interview/complete',
    {
      method: 'POST',
      body: JSON.stringify({
        interview_id: interviewId,
      }),
    }
  );
}

/**
 * Retrieve interview session details and history
 * GET /interview/{interview_id}
 */
export async function getInterviewDetail(
  interviewId: string
): Promise<BackendInterviewDetailResponse> {
  return await request<BackendInterviewDetailResponse>(`/interview/${encodeURIComponent(interviewId)}`);
}

/**
 * Fetch doctor's pre-consultation patient queue
 * GET /doctor/patients
 */
export async function getDoctorPatients(): Promise<PatientListItem[]> {
  return await request<PatientListItem[]>('/doctor/patients');
}

/**
 * Fetch doctor structured summary for a patient
 * GET /doctor/patients/{patient_id}/summary
 */
export async function getDoctorSummary(
  patientId: string
): Promise<DoctorSummaryResponse | null> {
  try {
    return await request<DoctorSummaryResponse>(
      `/doctor/patients/${encodeURIComponent(patientId)}/summary`
    );
  } catch (err: any) {
    if (err?.status === 404) return null;
    throw err;
  }
}

/**
 * Fetch doctor narrative summary generated by Gemini / fallback
 * GET /doctor/patients/{patient_id}/summary/narrative
 */
export async function getDoctorNarrative(
  patientId: string
): Promise<DoctorNarrativeResponse | null> {
  try {
    return await request<DoctorNarrativeResponse>(
      `/doctor/patients/${encodeURIComponent(patientId)}/summary/narrative`
    );
  } catch (err: any) {
    if (err?.status === 404) return null;
    throw err;
  }
}

/**
 * Update clinical summary fields with immutable audit tracking
 * PATCH /doctor/patients/{patient_id}/summary
 */
export async function updateDoctorSummary(
  patientId: string,
  changes: DoctorSummaryEditRequest,
  doctorId: string = 'doctor_demo'
): Promise<DoctorSummaryEditResponse> {
  return await request<DoctorSummaryEditResponse>(
    `/doctor/patients/${encodeURIComponent(patientId)}/summary`,
    {
      method: 'PATCH',
      headers: {
        'X-Doctor-ID': doctorId,
      },
      body: JSON.stringify(changes),
    }
  );
}

/**
 * Mark clinical summary as doctor-verified
 * POST /doctor/patients/{patient_id}/summary/verify
 */
export async function verifyDoctorSummary(
  patientId: string,
  doctorId: string = 'doctor_demo'
): Promise<DoctorSummaryVerifyResponse> {
  return await request<DoctorSummaryVerifyResponse>(
    `/doctor/patients/${encodeURIComponent(patientId)}/summary/verify`,
    {
      method: 'POST',
      headers: {
        'X-Doctor-ID': doctorId,
      },
    }
  );
}

/**
 * Retrieve doctor correction audit history
 * GET /doctor/patients/{patient_id}/summary/audit
 */
export async function getDoctorAudit(
  patientId: string
): Promise<DoctorEditAuditItem[]> {
  try {
    return await request<DoctorEditAuditItem[]>(
      `/doctor/patients/${encodeURIComponent(patientId)}/summary/audit`
    );
  } catch (err: any) {
    if (err?.status === 404) return [];
    throw err;
  }
}

/**
 * Backward compatibility helpers for doctor UI dashboard
 */
export async function getClinicalSummary(patientId: string): Promise<any> {
  const summary = await getDoctorSummary(patientId);
  if (summary) return summary;
  return null;
}

export async function approveSummary(patientId: string, doctorNotes?: string): Promise<any> {
  return await verifyDoctorSummary(patientId, 'doctor_demo');
}

export async function updatePatientSummary(patientId: string, data: any): Promise<any> {
  return await updateDoctorSummary(patientId, data, 'doctor_demo');
}

export async function getDashboardStats(): Promise<any> {
  try {
    const list = await getDoctorPatients();
    const verifiedCount = list.filter((p) => p.status === 'Verified').length;
    const priorityCount = list.filter((p) => p.priority === 'Priority' || p.priority === 'Urgent').length;
    return {
      patientsWaiting: list.length,
      interviewsCompleted: list.length,
      needsReview: list.length - verifiedCount,
      priorityReviews: priorityCount,
    };
  } catch {
    return {
      patientsWaiting: 1,
      interviewsCompleted: 1,
      needsReview: 1,
      priorityReviews: 0,
    };
  }
}

export async function completeInterview(patientId: string, extracted: any, transcript: any): Promise<any> {
  return { patient_id: patientId, status: 'Completed' };
}

export function resetDemoData(): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.removeItem('medisaarthi_current_patient_id');
    localStorage.removeItem('medisaarthi_selected_lang');
    localStorage.removeItem('medisaarthi_consent_given');
    localStorage.removeItem('medisaarthi_current_interview_id');
  } catch {}
}
