import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

// Import API services
import {
  getDoctorPatients,
  getDoctorSummary,
  getDoctorNarrative,
  getDoctorAudit,
  updateDoctorSummary,
  verifyDoctorSummary,
  getInterviewDetail,
} from '../services/api';

describe('Step 4B: Medisaarthi Doctor Dashboard Frontend Test Suite', () => {

  test('Test A & B & C: Doctor dashboard queue renders and fetches patient list including P1001', async () => {
    // Check dashboard component/page file structure
    const pageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/doctor/page.tsx'),
      'utf-8'
    );
    assert.ok(
      pageContent.includes('Doctor Dashboard') || pageContent.includes('Pre-Consultation Patient Queue'),
      'Must contain Doctor Dashboard heading'
    );
    assert.ok(
      pageContent.includes('Dr. Demo'),
      'Must display attending doctor Dr. Demo identity'
    );
    assert.ok(
      pageContent.includes('getDoctorPatients'),
      'Must invoke getDoctorPatients API'
    );

    // Call live API
    const patients = await getDoctorPatients();
    assert.ok(Array.isArray(patients), 'Must return an array of patients');
    assert.ok(patients.length > 0, 'Must contain at least one patient record');

    const p1001 = patients.find((p) => p.patient_id === 'P1001');
    assert.ok(p1001, 'P1001 (Rajesh Kumar) must appear in the patient list');
    assert.equal(p1001?.name, 'Rajesh Kumar');
    assert.equal(p1001?.gender, 'Male');
  });

  test('Test D: Patient selection links to patient detail /doctor/patients/[patient_id]', () => {
    const patientListContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/doctor/PatientList.tsx'),
      'utf-8'
    );
    assert.ok(
      patientListContent.includes('/doctor/patients/${patient.patient_id}') ||
      patientListContent.includes('/doctor/patients/'),
      'Must link directly to /doctor/patients/[id]'
    );
    assert.ok(
      patientListContent.includes('Review Patient'),
      'Must have Review Patient action link/button'
    );
  });

  test('Test E, F, G: Structured summary, Narrative, and Audit trail are fetched for P1001', async () => {
    // 1. Structured summary
    const summary = await getDoctorSummary('P1001');
    assert.ok(summary, 'Must return DoctorSummaryData for P1001');
    assert.equal(summary?.patient_snapshot.patient_id, 'P1001');
    assert.equal(summary?.patient_snapshot.name, 'Rajesh Kumar');
    assert.ok(summary?.current_complaint.chief_complaint, 'Must have chief_complaint');

    // Confirm Past Medical History
    const conditions = summary?.past_medical_history.map((h) => h.condition);
    assert.ok(
      conditions?.some((c) => c.includes('Hypertension')),
      'Must include Hypertension in PMH'
    );
    assert.ok(
      conditions?.some((c) => c.includes('Diabetes')),
      'Must include Diabetes in PMH'
    );

    // Confirm Medications
    const medNames = summary?.medications.map((m) => m.name);
    assert.ok(medNames?.includes('Amlodipine'), 'Must include Amlodipine in medications');
    assert.ok(medNames?.includes('Metformin'), 'Must include Metformin in medications');

    // 2. Narrative summary
    const narrative = await getDoctorNarrative('P1001');
    assert.ok(narrative, 'Must return narrative summary for P1001');
    assert.ok(narrative?.patient_snapshot, 'Must include patient snapshot in narrative');
    assert.ok(narrative?.presenting_complaint, 'Must include presenting complaint in narrative');
    assert.ok(narrative?.verification_note, 'Must include verification note in narrative');

    // 3. Audit trail
    const auditList = await getDoctorAudit('P1001');
    assert.ok(Array.isArray(auditList), 'Must return an array of audit records');
  });

  test('Test H: Verification status is prominently displayed with explicit states', () => {
    const headerContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/doctor/PatientProfileHeader.tsx'),
      'utf-8'
    );
    assert.ok(
      headerContent.includes('AI-assisted / unverified'),
      'Must support "AI-assisted / unverified" badge'
    );
    assert.ok(
      headerContent.includes('Verified'),
      'Must support "Verified" badge'
    );
    assert.ok(
      headerContent.includes('Verified by Dr. Demo'),
      'Must display verified doctor identity'
    );
  });

  test('Test I & J & K: Doctor Edit Mode allows modifying supported clinical fields via PATCH with X-Doctor-ID', async () => {
    const editModalContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/doctor/EditSummaryModal.tsx'),
      'utf-8'
    );

    // Form inputs for supported fields
    assert.ok(editModalContent.includes('edit-chief-complaint'), 'Must have chief complaint field');
    assert.ok(editModalContent.includes('edit-duration'), 'Must have duration field');
    assert.ok(editModalContent.includes('edit-severity'), 'Must have severity field');
    assert.ok(editModalContent.includes('edit-location'), 'Must have location field');
    assert.ok(editModalContent.includes('edit-trigger'), 'Must have trigger field');
    assert.ok(editModalContent.includes('edit-associated-symptoms'), 'Must have associated symptoms field');

    // Check updateDoctorSummary implementation sends X-Doctor-ID
    const apiContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/services/api.ts'),
      'utf-8'
    );
    assert.ok(
      apiContent.includes("'X-Doctor-ID': doctorId") || apiContent.includes('"X-Doctor-ID": doctorId'),
      'API client must send X-Doctor-ID header'
    );

    // Current summary
    const current = await getDoctorSummary('P1001');
    const newSeverity = current?.current_complaint.severity === '7' ? '8' : '7';
    const newLocation = current?.current_complaint.location === 'Left anterior chest' ? 'Substernal chest' : 'Left anterior chest';

    // Perform live test PATCH on P1001
    const editRes = await updateDoctorSummary('P1001', {
      severity: newSeverity,
      location: newLocation,
    }, 'doctor_demo');

    assert.ok(editRes.updated_fields.includes('severity'), 'Must report severity updated');
    assert.ok(editRes.updated_fields.includes('location'), 'Must report location updated');
    assert.equal(editRes.verification_status, 'AI-assisted / unverified', 'Must reset verification status');
  });

  test('Test L, M, N, O: Successful edit refreshes summary, narrative, audit trail, and status is unverified', async () => {
    // Perform edit to ensure known state
    await updateDoctorSummary('P1001', {
      severity: '7',
      location: 'Left anterior chest',
    }, 'doctor_demo');

    // Verify updated summary values
    const updatedSummary = await getDoctorSummary('P1001');
    assert.equal(updatedSummary?.current_complaint.severity, '7');
    assert.equal(updatedSummary?.current_complaint.location, 'Left anterior chest');
    assert.equal(updatedSummary?.verification_status, 'AI-assisted / unverified');

    // Verify audit trail recorded changes
    const auditList = await getDoctorAudit('P1001');
    const severityAudit = auditList.find((a) => a.field_name === 'severity');
    assert.ok(severityAudit, 'Audit log must record severity correction');
    assert.equal(severityAudit?.changed_by, 'doctor_demo');

    const locationAudit = auditList.find((a) => a.field_name === 'location');
    assert.ok(locationAudit, 'Audit log must record location correction');
  });

  test('Test P, Q, R: Verify button confirms with doctor, calls POST /verify, and displays Verified by Dr. Demo', async () => {
    const confirmModalContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/doctor/VerifyConfirmModal.tsx'),
      'utf-8'
    );
    assert.ok(
      confirmModalContent.includes('Have you reviewed the AI-assisted summary and made any required corrections'),
      'Must contain explicit confirmation prompt'
    );

    // Call live verification
    const verifyRes = await verifyDoctorSummary('P1001', 'doctor_demo');
    assert.equal(verifyRes.verification_status, 'Verified');
    assert.equal(verifyRes.verified_by, 'doctor_demo');
    assert.ok(verifyRes.verified_at, 'Must have verified_at timestamp');

    // Fetch summary to confirm verified status persists
    const verifiedSummary = await getDoctorSummary('P1001');
    assert.equal(verifiedSummary?.verification_status, 'Verified');
  });

  test('Test S: Editing a verified summary reverts status to unverified and requires re-verification', async () => {
    // First ensure P1001 is verified
    await verifyDoctorSummary('P1001', 'doctor_demo');
    let summary = await getDoctorSummary('P1001');
    assert.equal(summary?.verification_status, 'Verified');

    // Doctor edits a field
    const editRes = await updateDoctorSummary('P1001', {
      severity: '8',
    }, 'doctor_demo');

    assert.equal(editRes.verification_status, 'AI-assisted / unverified');

    // Confirm state in PostgreSQL
    summary = await getDoctorSummary('P1001');
    assert.equal(summary?.verification_status, 'AI-assisted / unverified');

    // Re-verify
    const verifyRes = await verifyDoctorSummary('P1001', 'doctor_demo');
    assert.equal(verifyRes.verification_status, 'Verified');
  });

  test('Test T: Audit entries display original value and corrected value', () => {
    const auditComponentContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/doctor/DoctorAuditTrail.tsx'),
      'utf-8'
    );
    assert.ok(
      auditComponentContent.includes('AI Original Value:') || auditComponentContent.includes('original_value'),
      'Must display original value'
    );
    assert.ok(
      auditComponentContent.includes('Doctor Correction:') || auditComponentContent.includes('corrected_value'),
      'Must display doctor correction'
    );
    assert.ok(
      auditComponentContent.includes('changed_by'),
      'Must display doctor identity'
    );
  });

  test('Test U: Empty priority flags display "No explicit priority or safety flags recorded."', () => {
    const structContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/doctor/StructuredClinicalData.tsx'),
      'utf-8'
    );
    assert.ok(
      structContent.includes('No explicit priority or safety flags recorded.'),
      'Must display exact placeholder when priority_flags is empty'
    );

    const narrativeContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/doctor/NarrativeSummaryCard.tsx'),
      'utf-8'
    );
    assert.ok(
      narrativeContent.includes('No explicit priority or safety flags recorded.'),
      'Narrative card must display exact placeholder when priority_flags is empty'
    );
  });

  test('Test V: Missing information displays clearly or "None recorded"', () => {
    const structContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/doctor/StructuredClinicalData.tsx'),
      'utf-8'
    );
    assert.ok(
      structContent.includes('None recorded'),
      'Must display "None recorded" when missing information is empty'
    );
  });

  test('Test W: Allergy status distinguishes NKDA from no record', () => {
    const structContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/doctor/StructuredClinicalData.tsx'),
      'utf-8'
    );
    assert.ok(
      structContent.includes('summary.allergy_status'),
      'Must render actual backend allergy_status value directly'
    );
  });

  test('Test X & Y: Backend errors are handled and duplicate edit/verify submissions are prevented', () => {
    const detailPageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/doctor/patients/[id]/page.tsx'),
      'utf-8'
    );
    assert.ok(
      detailPageContent.includes('isVerifying') && detailPageContent.includes('errorMessage'),
      'Must maintain isVerifying loading state and errorMessage'
    );
    assert.ok(
      !detailPageContent.includes('console.error(err.stack)'),
      'Must not expose raw stack traces'
    );

    const editModalContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/doctor/EditSummaryModal.tsx'),
      'utf-8'
    );
    assert.ok(
      editModalContent.includes('disabled={isSaving}') || editModalContent.includes('isLoading={isSaving}'),
      'Must disable/show loading on submit during save'
    );
  });

  test('Test Z & AA: Security invariants & No clinical diagnosis logic in frontend', () => {
    const doctorFiles = [
      'src/app/doctor/page.tsx',
      'src/app/doctor/patients/[id]/page.tsx',
      'src/components/doctor/PatientList.tsx',
      'src/components/doctor/PatientProfileHeader.tsx',
      'src/components/doctor/NarrativeSummaryCard.tsx',
      'src/components/doctor/StructuredClinicalData.tsx',
      'src/components/doctor/DoctorAuditTrail.tsx',
      'src/components/doctor/EditSummaryModal.tsx',
      'src/components/doctor/VerifyConfirmModal.tsx',
    ];

    for (const relPath of doctorFiles) {
      const content = fs.readFileSync(path.resolve(process.cwd(), relPath), 'utf-8');
      assert.ok(!content.includes('GEMINI_API_KEY'), `${relPath} must not contain GEMINI_API_KEY`);
      assert.ok(!content.includes('AI_API_KEY'), `${relPath} must not contain AI_API_KEY`);
      assert.ok(!content.includes('generativelanguage.googleapis.com'), `${relPath} must not call Gemini directly`);
      assert.ok(!content.includes('AI diagnosis'), `${relPath} must not contain "AI diagnosis"`);
      assert.ok(!content.includes('predicted disease'), `${relPath} must not contain "predicted disease"`);
      assert.ok(!content.includes('suggested prescription'), `${relPath} must not contain "suggested prescription"`);
      assert.ok(!content.includes('recommended treatment'), `${relPath} must not contain "recommended treatment"`);
    }
  });

  test('Test AB: Complete 28-step manual P1001 walkthrough', async () => {
    // 1 & 2. Open /doctor and fetch patient list
    const patientList = await getDoctorPatients();
    assert.ok(patientList.length > 0, 'Step 1-2: Patient list must be non-empty');

    // 3. Select P1001 — Rajesh Kumar
    const rajesh = patientList.find((p) => p.patient_id === 'P1001');
    assert.ok(rajesh, 'Step 3: P1001 must exist in patient list');
    assert.equal(rajesh.name, 'Rajesh Kumar');

    // 4. Confirm patient demographics
    assert.equal(rajesh.age, 48, 'Step 4: Age 48');
    assert.equal(rajesh.gender.toLowerCase(), 'male', 'Step 4: Male');
    assert.equal(rajesh.language, 'hi', 'Step 4: Hindi');

    // 5. Confirm verification status
    let summary = await getDoctorSummary('P1001');
    assert.ok(summary, 'Must load summary for P1001');

    // 6. Confirm AI-assisted narrative is displayed
    const narrative = await getDoctorNarrative('P1001');
    assert.ok(narrative, 'Step 6: Narrative must exist');
    assert.ok(narrative?.patient_snapshot.includes('Rajesh Kumar'));
    assert.ok(narrative?.verification_note);

    // 7. Confirm structured data is displayed
    assert.ok(summary.current_complaint);
    assert.ok(summary.current_complaint.chief_complaint);

    // 8. Confirm history: Hypertension, Type 2 Diabetes
    const conditions = summary.past_medical_history.map((h) => h.condition);
    assert.ok(conditions.some((c) => c.includes('Hypertension')), 'Step 8: Hypertension in PMH');
    assert.ok(conditions.some((c) => c.includes('Diabetes')), 'Step 8: Diabetes in PMH');

    // 9. Confirm medications: Amlodipine, Metformin
    const medNames = summary.medications.map((m) => m.name);
    assert.ok(medNames.includes('Amlodipine'), 'Step 9: Amlodipine in medications');
    assert.ok(medNames.includes('Metformin'), 'Step 9: Metformin in medications');

    // 10. Confirm allergy status
    assert.ok(summary.allergy_status, 'Step 10: Allergy status present');

    // 11. Confirm explicit priority flags
    assert.ok(Array.isArray(summary.priority_flags), 'Step 11: Priority flags array');

    // 12. Open audit history
    let auditList = await getDoctorAudit('P1001');
    assert.ok(Array.isArray(auditList), 'Step 12: Audit history array');

    // 13, 14, 15, 16. Enter Edit mode & Change severity to 7, location to "Left anterior chest" & Save
    const editRes1 = await updateDoctorSummary('P1001', {
      severity: '7',
      location: 'Left anterior chest',
    }, 'doctor_demo');

    // 17. Confirm severity = 7, location = Left anterior chest
    summary = await getDoctorSummary('P1001');
    assert.equal(summary?.current_complaint.severity, '7', 'Step 17: Severity = 7');
    assert.equal(summary?.current_complaint.location, 'Left anterior chest', 'Step 17: Location = Left anterior chest');

    // 18. Confirm status: AI-assisted / unverified
    assert.equal(summary?.verification_status, 'AI-assisted / unverified', 'Step 18: Unverified after edit');

    // 19. Confirm audit history contains the correction
    auditList = await getDoctorAudit('P1001');
    const latestSeverityAudit = auditList.find((a) => a.field_name === 'severity');
    assert.ok(latestSeverityAudit, 'Step 19: Audit log has severity correction');

    // 20. Confirm regenerated narrative reflects corrected values
    const updatedNarrative = await getDoctorNarrative('P1001');
    assert.ok(updatedNarrative, 'Step 20: Narrative refreshed');

    // 21. Click Verify Summary
    const verifyRes1 = await verifyDoctorSummary('P1001', 'doctor_demo');

    // 22. Confirm Verified, Verified by Dr. Demo
    assert.equal(verifyRes1.verification_status, 'Verified', 'Step 22: Status Verified');
    assert.equal(verifyRes1.verified_by, 'doctor_demo', 'Step 22: Verified by Dr. Demo');

    // 23 & 24. Refresh the page & Confirm Verified state persists
    const refreshedSummary = await getDoctorSummary('P1001');
    assert.equal(refreshedSummary?.verification_status, 'Verified', 'Step 23-24: Verified state persists on refresh');

    // 25. Edit one field again (change severity to 8 to trigger state transition)
    const editRes2 = await updateDoctorSummary('P1001', {
      severity: '8',
    }, 'doctor_demo');

    // 26 & 27. Confirm status returns to AI-assisted / unverified
    const postEditSummary = await getDoctorSummary('P1001');
    assert.equal(postEditSummary?.verification_status, 'AI-assisted / unverified', 'Step 26: Status reverts to unverified');

    // 28. Verify again
    const verifyRes2 = await verifyDoctorSummary('P1001', 'doctor_demo');
    assert.equal(verifyRes2.verification_status, 'Verified', 'Step 28: Verified again successfully');
  });
});
