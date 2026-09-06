import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

// Import services and mock data
import {
  getPatient,
  getPatients,
  startInterviewSession,
  respondToInterviewSession,
  completeInterviewSession,
  getDoctorSummary,
} from '../services/api';
import { INITIAL_PATIENTS } from '../lib/mock-data';

describe('Step 4A: Medisaarthi Patient Interview Frontend Test Suite', () => {

  test('Test A: Welcome screen definitions and copy', () => {
    const welcomePageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/page.tsx'),
      'utf-8'
    );
    assert.ok(
      welcomePageContent.includes('Welcome to Medisaarthi'),
      'Must contain English welcome heading'
    );
    assert.ok(
      welcomePageContent.includes('Before you meet the doctor, Medisaarthi will ask you a few questions about your health.'),
      'Must contain the required explanation'
    );
    assert.ok(
      welcomePageContent.includes('Start / शुरू करें') || welcomePageContent.includes('Start'),
      'Must have Start button'
    );
  });

  test('Test B & C: Patient Identification & Demo Patient P1001 Selection', async () => {
    // Demo patient P1001 exists
    const demoPatient = INITIAL_PATIENTS.find((p) => p.patient_id === 'P1001');
    assert.ok(demoPatient, 'P1001 demo profile must exist in initial profiles');
    assert.equal(demoPatient.name, 'Rajesh Kumar');

    // Retrieve from API service
    const patientFromApi = await getPatient('P1001');
    assert.ok(patientFromApi, 'API must return patient P1001');
    assert.equal(patientFromApi.patient_id, 'P1001');
  });

  test('Test D: Language selection options', () => {
    const langPageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/language/page.tsx'),
      'utf-8'
    );
    assert.ok(langPageContent.includes('Language'), 'Language selection page must exist');

    const selectorContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/components/patient/LanguageSelector.tsx'),
      'utf-8'
    );
    assert.ok(selectorContent.includes('हिंदी') && selectorContent.includes('English'), 'Must support Hindi and English');
  });

  test('Test E: Consent screen clear explanation and agreement requirement', () => {
    const consentContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/consent/page.tsx'),
      'utf-8'
    );
    assert.ok(
      consentContent.includes('Medisaarthi will ask questions about your current health problem and your medical history. Your answers will be shared with the doctor for review.'),
      'Consent explanation must match required phrasing'
    );
    assert.ok(
      consentContent.includes('I Agree & Continue'),
      'Must contain I Agree & Continue button'
    );
    assert.ok(
      consentContent.includes('Go Back'),
      'Must contain Go Back button'
    );
  });

  test('Test F & G: POST /interview/start returns initial question and session', { timeout: 60000 }, async () => {
    const startRes = await startInterviewSession('P1001', 'hi');
    assert.ok(startRes.interview_id, 'Must return interview_id');
    assert.equal(startRes.status, 'active', 'Interview status must be active');
    assert.ok(startRes.initial_question?.text, 'Must provide initial question text');
    assert.ok(
      startRes.initial_question.text.includes('नमस्ते') || startRes.initial_question.text.includes('अस्पताल'),
      'Initial question in Hindi must be clinically appropriate'
    );
  });

  test('Test H & I: POST /interview/respond receives answer and returns adaptive question', { timeout: 60000 }, async () => {
    const startRes = await startInterviewSession('P1001', 'hi');
    const interviewId = startRes.interview_id;

    // Send first answer: chest pain
    const replyRes = await respondToInterviewSession(interviewId, 'Mujhe seene mein dard hai, 3 din se');
    assert.equal(replyRes.interview_id, interviewId);
    assert.ok(replyRes.next_question?.text, 'Must return next question');
    assert.ok(replyRes.extracted_facts.length > 0, 'Must return extracted facts');

    // Confirm chief complaint fact was extracted
    const ccFact = replyRes.extracted_facts.find((f) => f.field_name === 'chief_complaint');
    assert.ok(ccFact, 'Must extract chief_complaint');
  });

  test('Test J: Multiple responses progress the adaptive interview', { timeout: 60000 }, async () => {
    const startRes = await startInterviewSession('P1001', 'hi');
    const interviewId = startRes.interview_id;

    // Turn 1
    const res1 = await respondToInterviewSession(interviewId, 'Seene mein dard hai, 3 din se');
    assert.ok(res1.next_question.text);

    // Turn 2
    const res2 = await respondToInterviewSession(interviewId, 'Dard bahut tej hai 8 out of 10');
    assert.ok(res2.next_question.text);
  });


  test('Test K: Loading state / duplicate submission prevention in UI', () => {
    const interviewPageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/interview/page.tsx'),
      'utf-8'
    );
    assert.ok(
      interviewPageContent.includes('isSubmitting') && interviewPageContent.includes('disabled={!inputText.trim() || isSubmitting'),
      'Must disable submit button while isSubmitting is true'
    );
    assert.ok(
      interviewPageContent.includes('Please wait') || interviewPageContent.includes('प्रतीक्षा करें'),
      'Must display loading text while submitting'
    );
  });

  test('Test L: Human readable error handling without leaking stack traces or internal secrets', () => {
    const interviewPageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/interview/page.tsx'),
      'utf-8'
    );
    assert.ok(
      interviewPageContent.includes('errorMessage') && interviewPageContent.includes('Retry'),
      'Must have friendly error message banner with retry capability'
    );
    assert.ok(
      !interviewPageContent.includes('console.error(err.stack)'),
      'Must not expose stack traces to user'
    );
  });

  test('Test M: Completion screen has no diagnosis, prescriptions, or treatment recommendations', () => {
    const completedPageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/completed/page.tsx'),
      'utf-8'
    );
    assert.ok(
      completedPageContent.includes('Thank you.') || completedPageContent.includes('धन्यवाद।'),
      'Must have thank you heading'
    );
    assert.ok(
      completedPageContent.includes('Your information has been recorded and will be available to the doctor for review.') ||
      completedPageContent.includes('आपकी जानकारी सुरक्षित रूप से दर्ज कर ली गई है'),
      'Must have standard completion notice'
    );
    assert.ok(
      !completedPageContent.includes('prescribe') &&
      !completedPageContent.includes('Prescription') &&
      !completedPageContent.includes('treatment plan') &&
      !completedPageContent.includes('You may have:'),
      'Must never display diagnosis or prescriptions'
    );
  });

  test('Test N & O: Hindi and English UI labels supported', () => {
    const interviewContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/interview/page.tsx'),
      'utf-8'
    );
    assert.ok(interviewContent.includes('isHindi'), 'Must support language-dependent UI strings');
    assert.ok(interviewContent.includes('वर्तमान प्रश्न:'), 'Must include Hindi UI label');
    assert.ok(interviewContent.includes('Current Question:'), 'Must include English UI label');
  });

  test('Test P & Q: Security invariants — Gemini never called directly from frontend, no secrets in source', () => {
    const filesToCheck = [
      'src/services/api.ts',
      'src/lib/api.ts',
      'src/app/patient/page.tsx',
      'src/app/patient/identify/page.tsx',
      'src/app/patient/language/page.tsx',
      'src/app/patient/consent/page.tsx',
      'src/app/patient/interview/page.tsx',
      'src/app/patient/completed/page.tsx',
    ];

    for (const relPath of filesToCheck) {
      const content = fs.readFileSync(path.resolve(process.cwd(), relPath), 'utf-8');
      assert.ok(!content.includes('GEMINI_API_KEY'), `${relPath} must not contain GEMINI_API_KEY`);
      assert.ok(!content.includes('AI_API_KEY'), `${relPath} must not contain AI_API_KEY`);
      assert.ok(!content.includes('generativelanguage.googleapis.com'), `${relPath} must not call Gemini directly`);
    }
  });

  test('Test R: Explicit completion endpoint works', async () => {
    const startRes = await startInterviewSession('P1001', 'en');
    const compRes = await completeInterviewSession(startRes.interview_id);
    assert.equal(compRes.interview_id, startRes.interview_id);
    assert.equal(compRes.status, 'completed');
  });
});
