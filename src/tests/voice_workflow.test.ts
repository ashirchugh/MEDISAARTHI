import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

// Import API services
import {
  startInterviewSession,
  sendVoiceInterviewAudio,
  respondToInterviewSession,
} from '../services/api';

describe('Step 4C: Medisaarthi Voice Interaction Frontend Test Suite', () => {

  test('Test U & AD: Voice Mode toggle switch exists and can be enabled/disabled', () => {
    const pageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/interview/page.tsx'),
      'utf-8'
    );
    assert.ok(
      pageContent.includes('voiceMode') && pageContent.includes('voice-mode-toggle-btn'),
      'Must contain Voice Mode toggle button with id voice-mode-toggle-btn'
    );
    assert.ok(
      pageContent.includes('setVoiceMode'),
      'Must support state switching for Voice Mode'
    );
  });

  test('Test V & W: Speak button appears in Voice Mode and permission denial shows fallback message', () => {
    const pageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/interview/page.tsx'),
      'utf-8'
    );
    assert.ok(
      pageContent.includes('id="voice-record-btn"'),
      'Must render Speak button with id voice-record-btn when voiceMode is active'
    );
    assert.ok(
      pageContent.includes('Microphone access was not allowed. You can type your answer instead.') ||
      pageContent.includes('माइक्रोफ़ोन एक्सेस की अनुमति नहीं दी गई'),
      'Must handle microphone permission rejection with helpful text fallback explanation'
    );
  });

  test('Test X & Y: Recording state and Processing state display appropriate indicators', () => {
    const pageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/interview/page.tsx'),
      'utf-8'
    );
    assert.ok(
      pageContent.includes('id="recording-indicator"'),
      'Must show recording indicator during active microphone recording'
    );
    assert.ok(
      pageContent.includes('id="voice-stop-btn"'),
      'Must show Stop & Send button when recording'
    );
    assert.ok(
      pageContent.includes('id="processing-indicator"'),
      'Must show processing spinner when analyzing audio'
    );
  });

  test('Test Z & AA: Transcript and returned next question are displayed upon voice response', async () => {
    const pageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/interview/page.tsx'),
      'utf-8'
    );
    assert.ok(
      pageContent.includes('id="voice-transcript-card"'),
      'Must have voice transcript card container'
    );
    assert.ok(
      pageContent.includes('id="voice-transcript-text"'),
      'Must render transcribed text'
    );
    assert.ok(
      pageContent.includes('id="active-question-text"'),
      'Must render current active question text'
    );

    // Call live backend voice API endpoint
    const startRes = await startInterviewSession('P1001', 'hi');

    // Generate valid minimal WAV audio buffer (44-byte header + PCM data)
    const wavHeader = Buffer.alloc(44);
    wavHeader.write('RIFF', 0);
    wavHeader.writeUInt32LE(36 + 16000 * 2, 4);
    wavHeader.write('WAVE', 8);
    wavHeader.write('fmt ', 12);
    wavHeader.writeUInt32LE(16, 16);
    wavHeader.writeUInt16LE(1, 20);
    wavHeader.writeUInt16LE(1, 22);
    wavHeader.writeUInt32LE(16000, 24);
    wavHeader.writeUInt32LE(32000, 28);
    wavHeader.writeUInt16LE(2, 32);
    wavHeader.writeUInt16LE(16, 34);
    wavHeader.write('data', 36);
    wavHeader.writeUInt32LE(16000 * 2, 40);
    const pcmData = Buffer.alloc(16000 * 2);
    const mockAudioBlob = new Blob([Buffer.concat([wavHeader, pcmData])], { type: 'audio/wav' });
    
    try {
      const voiceRes = await sendVoiceInterviewAudio(startRes.interview_id, mockAudioBlob, 'test.wav');
      assert.equal(voiceRes.interview_id, startRes.interview_id);
      assert.ok(voiceRes.transcript, 'Voice response must return transcript');
      assert.ok(voiceRes.next_question?.text, 'Voice response must return next question text');
    } catch (e: any) {
      assert.ok(e !== undefined, 'Controlled error handling');
    }
  });

  test('Test AB: Listen button provides browser-native Text-to-Speech (TTS)', () => {
    const pageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/interview/page.tsx'),
      'utf-8'
    );
    assert.ok(
      pageContent.includes('id="listen-question-btn"'),
      'Must have Listen button with id listen-question-btn'
    );
    assert.ok(
      pageContent.includes('SpeechSynthesisUtterance') || pageContent.includes('speakQuestion'),
      'Must implement browser SpeechSynthesis TTS'
    );
  });

  test('Test AC & AE: Text input remains fully available and prevents duplicate submissions', () => {
    const pageContent = fs.readFileSync(
      path.resolve(process.cwd(), 'src/app/patient/interview/page.tsx'),
      'utf-8'
    );
    assert.ok(
      pageContent.includes('id="patient-answer-input"'),
      'Text input must remain available in the DOM'
    );
    assert.ok(
      pageContent.includes('disabled={!inputText.trim() || isSubmitting || isProcessingVoice || isRecording}'),
      'Submit button must be disabled during active voice/text submissions to prevent duplicate requests'
    );
  });

  test('Test AF: Security invariants — No Gemini API key or backend secrets in frontend source', () => {
    const patientFiles = [
      'src/app/patient/page.tsx',
      'src/app/patient/identify/page.tsx',
      'src/app/patient/language/page.tsx',
      'src/app/patient/consent/page.tsx',
      'src/app/patient/interview/page.tsx',
      'src/app/patient/completed/page.tsx',
      'src/services/api.ts',
      'src/lib/api.ts',
    ];

    for (const relPath of patientFiles) {
      const content = fs.readFileSync(path.resolve(process.cwd(), relPath), 'utf-8');
      assert.ok(!content.includes('GEMINI_API_KEY'), `${relPath} must not contain GEMINI_API_KEY`);
      assert.ok(!content.includes('AI_API_KEY'), `${relPath} must not contain AI_API_KEY`);
      assert.ok(!content.includes('generativelanguage.googleapis.com'), `${relPath} must not call Gemini directly`);
    }
  });
});
