'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  Patient,
  Language,
  InterviewMessage,
  ExtractedFactItem,
  ExtractedSymptomData,
} from '@/types';
import { INITIAL_PATIENTS } from '@/lib/mock-data';
import {
  startInterviewSession,
  respondToInterviewSession,
  sendVoiceInterviewAudio,
  completeInterviewSession,
  getPatient,
} from '@/services/api';
import { PatientHeader } from '@/components/patient/PatientHeader';
import { InterviewProgress } from '@/components/patient/InterviewProgress';
import { ExtractedInfo } from '@/components/patient/ExtractedInfo';
import { Button } from '@/components/ui/Button';
import {
  Send,
  Bot,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  RefreshCw,
  Sparkles,
  CheckCircle2,
  HelpCircle,
  Mic,
  MicOff,
  Square,
  Volume2,
  VolumeX,
  Radio,
} from 'lucide-react';

export default function PatientInterviewPage() {
  const router = useRouter();

  // Core State
  const [patient, setPatient] = useState<Patient>(INITIAL_PATIENTS[0]);
  const [language, setLanguage] = useState<Language>('hi');
  const [interviewId, setInterviewId] = useState<string>('');
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [messages, setMessages] = useState<InterviewMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [isInitializing, setIsInitializing] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [interviewCompleted, setInterviewCompleted] = useState<boolean>(false);
  const [questionCount, setQuestionCount] = useState<number>(1);

  // Voice Interaction State (Step 4C)
  const [voiceMode, setVoiceMode] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isProcessingVoice, setIsProcessingVoice] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [recordingSeconds, setRecordingSeconds] = useState<number>(0);
  const [lastTranscript, setLastTranscript] = useState<string | null>(null);

  // Extracted structured facts from backend
  const [extractedData, setExtractedData] = useState<ExtractedSymptomData>({
    chief_complaint: '',
    duration: '',
    severity: '',
    associated_symptoms: [],
  });

  const inputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const isHindi = language === 'hi';

  // 1. Text-to-Speech (TTS) using browser window.speechSynthesis
  const speakQuestion = (textToSpeak: string) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;

    try {
      window.speechSynthesis.cancel(); // Cancel previous utterances
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      utterance.lang = isHindi ? 'hi-IN' : 'en-IN';
      utterance.rate = 0.95; // Clear and accessible pace
      utterance.pitch = 1.0;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    } catch {
      setIsSpeaking(false);
    }
  };

  const stopSpeaking = () => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  // 2. Initialize Interview with Backend
  const initializeInterview = async () => {
    setIsInitializing(true);
    setErrorMessage(null);

    let currentId = 'P1001';
    let currentLang: Language = 'hi';

    try {
      const storedId = localStorage.getItem('medisaarthi_current_patient_id');
      const storedLang = localStorage.getItem('medisaarthi_selected_lang');
      if (storedId) currentId = storedId;
      if (storedLang === 'en' || storedLang === 'hi') currentLang = storedLang;
    } catch {}

    setLanguage(currentLang);

    try {
      const p = (await getPatient(currentId)) || INITIAL_PATIENTS[0];
      setPatient(p);

      // Call Backend POST /interview/start
      const startRes = await startInterviewSession(p.patient_id, currentLang);
      setInterviewId(startRes.interview_id);

      try {
        localStorage.setItem('medisaarthi_current_interview_id', startRes.interview_id);
      } catch {}

      const initialQ =
        startRes.initial_question?.text ||
        (currentLang === 'hi'
          ? `नमस्ते ${p.name} जी। आपको किस वजह से आज अस्पताल आना पड़ा?`
          : `Hello ${p.name}. What brings you to the hospital today?`);

      setCurrentQuestion(initialQ);

      const initialMsg: InterviewMessage = {
        id: `msg-${Date.now()}`,
        sender: 'ai',
        text: initialQ,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages([initialMsg]);
      setIsInitializing(false);

      if (voiceMode) {
        speakQuestion(initialQ);
      }
    } catch (err: any) {
      setIsInitializing(false);
      setErrorMessage(
        isHindi
          ? 'सर्वर से कनेक्ट करने में असमर्थ। कृपया जांचें कि बैकएंड चालू है और पुनः प्रयास करें।'
          : 'Unable to connect to the Medisaarthi server. Please ensure the backend is running and try again.'
      );
    }
  };

  useEffect(() => {
    initializeInterview();
  }, []);

  // Cleanup timers & speech synthesis on unmount
  useEffect(() => {
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      stopSpeaking();
    };
  }, []);

  // Focus input whenever question changes
  useEffect(() => {
    if (!isInitializing && !isSubmitting && !isProcessingVoice && !interviewCompleted) {
      inputRef.current?.focus();
    }
  }, [currentQuestion, isInitializing, isSubmitting, isProcessingVoice, interviewCompleted]);

  // Helper to sync extracted facts from backend into ExtractedSymptomData UI state
  const updateExtractedFromFacts = (facts: ExtractedFactItem[]) => {
    setExtractedData((prev) => {
      const next = { ...prev };
      for (const f of facts) {
        if (f.field_name === 'chief_complaint') next.chief_complaint = f.value;
        else if (f.field_name === 'duration') next.duration = f.value;
        else if (f.field_name === 'severity') next.severity = f.value;
        else if (f.field_name === 'location') next.location = f.value;
        else if (f.field_name === 'associated_symptoms') {
          if (!next.associated_symptoms.includes(f.value)) {
            next.associated_symptoms = [...next.associated_symptoms, f.value];
          }
        }
      }
      return next;
    });
  };

  // 3. Submit Patient Text Answer to Backend
  const handleSendResponse = async (textToSend?: string) => {
    const message = (textToSend !== undefined ? textToSend : inputText).trim();
    if (!message || isSubmitting || isProcessingVoice || !interviewId || interviewCompleted) return;

    stopSpeaking();
    setInputText('');
    setIsSubmitting(true);
    setErrorMessage(null);

    // Append patient message to transcript
    const patientMsg: InterviewMessage = {
      id: `pat-${Date.now()}`,
      sender: 'patient',
      text: message,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    const updatedMessages = [...messages, patientMsg];
    setMessages(updatedMessages);

    try {
      // Call Backend POST /interview/respond
      const respondRes = await respondToInterviewSession(interviewId, message);

      if (respondRes.extracted_facts && respondRes.extracted_facts.length > 0) {
        updateExtractedFromFacts(respondRes.extracted_facts);
      }

      const nextQText = respondRes.next_question?.text || '';
      setCurrentQuestion(nextQText);
      setQuestionCount((c) => c + 1);

      const aiReplyMsg: InterviewMessage = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: nextQText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages([...updatedMessages, aiReplyMsg]);

      if (voiceMode && nextQText) {
        speakQuestion(nextQText);
      }

      // If backend reports completion
      if (respondRes.interview_completed || respondRes.status === 'completed') {
        setInterviewCompleted(true);
      }
      setIsSubmitting(false);
    } catch (err: any) {
      setIsSubmitting(false);
      setErrorMessage(
        isHindi
          ? 'उत्तर भेजने में समस्या आई। कृपया पुनः प्रयास करें।'
          : 'Could not send response. Please try again.'
      );
    }
  };

  // 4. Voice Recording using MediaRecorder API (Step 4C)
  const handleStartRecording = async () => {
    if (isRecording || isProcessingVoice || isSubmitting || interviewCompleted) return;

    stopSpeaking();
    setErrorMessage(null);
    audioChunksRef.current = [];

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setErrorMessage(
          isHindi
            ? 'आपके ब्राउज़र में माइक्रोफ़ोन समर्थित नहीं है। आप लिखकर उत्तर दे सकते हैं।'
            : 'Microphone access is not supported in this browser. You can type your answer instead.'
        );
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : MediaRecorder.isTypeSupported('audio/mp4')
        ? 'audio/mp4'
        : 'audio/wav';

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Stop all audio stream tracks
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        if (audioBlob.size > 0) {
          await handleSendVoiceAudio(audioBlob, mimeType);
        } else {
          setIsProcessingVoice(false);
        }
      };

      mediaRecorder.start(250); // Slice data every 250ms
      setIsRecording(true);
      setRecordingSeconds(0);

      // Start duration counter
      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      setIsRecording(false);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      setErrorMessage(
        isHindi
          ? 'माइक्रोफ़ोन एक्सेस की अनुमति नहीं दी गई। आप लिखकर उत्तर दे सकते हैं।'
          : 'Microphone access was not allowed. You can type your answer instead.'
      );
    }
  };

  const handleStopRecording = () => {
    if (!isRecording || !mediaRecorderRef.current) return;

    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }

    setIsRecording(false);
    setIsProcessingVoice(true);
    mediaRecorderRef.current.stop();
  };

  // 5. Send Audio to POST /interview/{interview_id}/voice
  const handleSendVoiceAudio = async (audioBlob: Blob, mimeType: string) => {
    if (!interviewId || interviewCompleted) return;

    setIsProcessingVoice(true);
    setErrorMessage(null);

    try {
      const voiceRes = await sendVoiceInterviewAudio(
        interviewId,
        audioBlob,
        `patient_voice.${mimeType.includes('webm') ? 'webm' : 'wav'}`
      );

      const transcript = voiceRes.transcript || voiceRes.received_message;
      setLastTranscript(transcript);

      // Append transcribed patient speech to message log
      const patientMsg: InterviewMessage = {
        id: `pat-voice-${Date.now()}`,
        sender: 'patient',
        text: transcript,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      const updatedMessages = [...messages, patientMsg];
      setMessages(updatedMessages);

      if (voiceRes.extracted_facts && voiceRes.extracted_facts.length > 0) {
        updateExtractedFromFacts(voiceRes.extracted_facts);
      }

      const nextQText = voiceRes.next_question?.text || '';
      setCurrentQuestion(nextQText);
      setQuestionCount((c) => c + 1);

      const aiReplyMsg: InterviewMessage = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: nextQText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages([...updatedMessages, aiReplyMsg]);

      // Speak next question in Voice Mode
      if (voiceMode && nextQText) {
        speakQuestion(nextQText);
      }

      if (voiceRes.interview_completed || voiceRes.status === 'completed') {
        setInterviewCompleted(true);
      }
      setIsProcessingVoice(false);
    } catch (err: any) {
      setIsProcessingVoice(false);
      setErrorMessage(
        err?.message ||
          (isHindi
            ? 'आवाज़ पहचानने में समस्या आई। कृपया पुनः बोलें या लिखकर उत्तर दें।'
            : 'Could not process voice recording. Please speak clearly or type your answer.')
      );
    }
  };

  // 6. Complete Interview & Navigate to Screen 6
  const handleFinishInterview = async () => {
    stopSpeaking();
    if (interviewId) {
      try {
        await completeInterviewSession(interviewId);
      } catch {}
    }
    router.push('/patient/completed');
  };

  // Quick suggestions for low-literacy / quick testing
  const demoQuickResponses = isHindi
    ? [
        'सीने में दर्द है, 3 दिन से',
        'दर्द बहुत तेज है (8/10)',
        'चलने पर दर्द बढ़ जाता है',
        'पसीना आ रहा है',
        'नहीं, कोई अन्य लक्षण नहीं',
      ]
    : [
        'Chest pain for 3 days',
        'Severe pain, 8 out of 10',
        'Worsens when walking',
        'Sweating and shortness of breath',
        'No other complaints',
      ];

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-between text-slate-900">
      <PatientHeader currentStep={4} totalSteps={4} stepName="Interview" />

      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 w-full flex flex-col gap-6 justify-center">
        {/* Progress Header */}
        <InterviewProgress
          collectedCount={questionCount}
          estimatedTotal={6}
          language={language}
        />

        {/* Error Banner */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-50 border-2 border-rose-300 text-rose-900 flex items-center justify-between gap-3 animate-in fade-in shadow-sm" id="interview-error-banner">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
              <span className="text-sm font-semibold">{errorMessage}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={initializeInterview}
              leftIcon={<RefreshCw className="w-4 h-4" />}
              className="bg-white border-rose-300 text-rose-800 hover:bg-rose-100 shrink-0"
              id="retry-interview-button"
            >
              {isHindi ? 'पुनः प्रयास करें (Retry)' : 'Retry'}
            </Button>
          </div>
        )}

        {/* Initializing Loading State */}
        {isInitializing ? (
          <div className="bg-white rounded-3xl border border-slate-200 shadow-md p-10 sm:p-14 text-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-sky-600 text-white mx-auto flex items-center justify-center animate-pulse shadow-md">
              <Bot className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">
              {isHindi ? 'इंटरव्यू शुरू हो रहा है...' : 'Starting your interview...'}
            </h2>
            <p className="text-slate-500 text-sm">
              {isHindi
                ? 'कृपया प्रतीक्षा करें, हम आपके डॉक्टर के लिए सत्र तैयार कर रहे हैं।'
                : 'Connecting with the clinical engine. Please wait...'}
            </p>
          </div>
        ) : interviewCompleted ? (
          /* Interview Completed Banner & CTA */
          <div className="bg-white rounded-3xl border-2 border-emerald-500 shadow-xl p-8 sm:p-12 text-center space-y-6 animate-in fade-in">
            <div className="w-20 h-20 rounded-3xl bg-emerald-600 text-white mx-auto flex items-center justify-center shadow-lg shadow-emerald-600/20 ring-8 ring-emerald-50">
              <CheckCircle2 className="w-10 h-10" />
            </div>

            <div className="space-y-2">
              <div className="text-xs font-black tracking-wider uppercase text-emerald-700">
                {isHindi ? 'इंटरव्यू संपन्न' : 'INTERVIEW COMPLETE'}
              </div>
              <h2 className="text-3xl font-black text-slate-900">
                {isHindi ? 'धन्यवाद! आपकी जानकारी दर्ज कर ली गई है।' : 'Thank you! Your information is recorded.'}
              </h2>
              <p className="text-base text-slate-600 max-w-lg mx-auto">
                {isHindi
                  ? 'आपकी सभी जानकारियां सुरक्षित रूप से संकलित कर डॉक्टर की समीक्षा के लिए तैयार कर दी गई हैं।'
                  : 'Your pre-consultation information has been recorded and will be available to the doctor for review.'}
              </p>
            </div>

            <div className="pt-4 max-w-md mx-auto">
              <Button
                variant="success"
                size="xl"
                onClick={handleFinishInterview}
                rightIcon={<ArrowRight className="w-5 h-5" />}
                className="w-full text-lg font-bold shadow-lg rounded-2xl py-4 min-h-[60px]"
                id="view-completed-button"
              >
                {isHindi ? 'समाप्त करें एवं आगे बढ़ें' : 'Finish & Continue'}
              </Button>
            </div>
          </div>
        ) : (
          /* Main Prominent Single Question Card */
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            {/* Left 2 Cols: The Active Question & Voice / Text Controls */}
            <div className="md:col-span-2 bg-white rounded-3xl border-2 border-sky-300 shadow-lg p-6 sm:p-8 space-y-6">
              {/* Question Header & Voice Mode Toggle */}
              <div className="flex flex-wrap items-center justify-between border-b border-slate-100 pb-3 gap-2">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-sky-600 text-white flex items-center justify-center font-bold shadow-xs">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-sky-900 block">
                      Medisaarthi AI Assistant
                    </span>
                    <span className="text-xs text-slate-500 block">
                      {isHindi ? `मरीज: ${patient.name}` : `Patient: ${patient.name}`}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2.5">
                  {/* Voice Mode ON/OFF Switch */}
                  <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl">
                    <Radio className={`w-3.5 h-3.5 ${voiceMode ? 'text-rose-600 animate-pulse' : 'text-slate-400'}`} />
                    <span className="text-xs font-bold text-slate-700">
                      {isHindi ? 'वॉइस मोड (Voice Mode):' : 'Voice Mode:'}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        const newMode = !voiceMode;
                        setVoiceMode(newMode);
                        if (!newMode) stopSpeaking();
                        else speakQuestion(currentQuestion);
                      }}
                      className={`px-2.5 py-0.5 rounded-lg text-xs font-extrabold transition-colors cursor-pointer ${
                        voiceMode
                          ? 'bg-rose-600 text-white shadow-xs'
                          : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                      }`}
                      id="voice-mode-toggle-btn"
                    >
                      {voiceMode ? 'ON' : 'OFF'}
                    </button>
                  </div>

                  <span className="px-3 py-1.5 rounded-xl bg-sky-100 text-sky-800 text-xs font-bold">
                    {isHindi ? `प्रश्न #${questionCount}` : `Question #${questionCount}`}
                  </span>
                </div>
              </div>

              {/* The Prominent Active Question */}
              <div className="space-y-2.5 py-1">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    {isHindi ? 'वर्तमान प्रश्न:' : 'Current Question:'}
                  </div>

                  {/* Listen Question Button */}
                  <button
                    type="button"
                    onClick={() => speakQuestion(currentQuestion)}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100 transition-colors cursor-pointer shadow-2xs"
                    id="listen-question-btn"
                  >
                    <Volume2 className={`w-4 h-4 ${isSpeaking ? 'text-sky-600 animate-pulse' : 'text-sky-700'}`} />
                    <span>{isSpeaking ? (isHindi ? 'बोल रहे हैं...' : 'Speaking...') : (isHindi ? '🔊 सुनें (Listen)' : '🔊 Listen')}</span>
                  </button>
                </div>

                <h1
                  className="text-2xl sm:text-3xl font-extrabold text-slate-900 leading-snug tracking-tight"
                  id="active-question-text"
                >
                  {currentQuestion}
                </h1>
                <p className="text-xs text-slate-500 font-medium">
                  {voiceMode
                    ? isHindi
                      ? 'माइक बटन दबाकर बोलें या नीचे लिखकर उत्तर दें।'
                      : 'Tap the Speak button to answer by voice, or type below.'
                    : isHindi
                    ? 'नीचे दिए गए बॉक्स में अपना उत्तर लिखें और आगे बढ़ें दबाएं।'
                    : 'Type your answer below and press Continue to proceed.'}
                </p>
              </div>

              {/* Voice Mode Primary Controller (Step 4C) */}
              {voiceMode && (
                <div className="p-5 rounded-2xl bg-gradient-to-tr from-sky-50 to-indigo-50/60 border-2 border-sky-200 space-y-4 shadow-sm" id="voice-interaction-panel">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold uppercase tracking-wider text-sky-900 flex items-center gap-2">
                      <Mic className="w-4 h-4 text-sky-600" />
                      <span>{isHindi ? 'ध्वनि उत्तर (Voice Input)' : 'Voice Input Controller'}</span>
                    </span>
                    {isRecording && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-100 border border-rose-300 text-rose-900 text-xs font-bold animate-pulse" id="recording-indicator">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-600" />
                        <span>{isHindi ? `रिकॉर्डिंग... (${recordingSeconds}s)` : `Recording... (${recordingSeconds}s)`}</span>
                      </span>
                    )}
                  </div>

                  {/* Main Record / Stop Action Bar */}
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3 pt-1">
                    {!isRecording ? (
                      <Button
                        type="button"
                        variant="primary"
                        size="xl"
                        onClick={handleStartRecording}
                        disabled={isProcessingVoice || isSubmitting}
                        leftIcon={<Mic className="w-6 h-6 text-white" />}
                        className="w-full sm:w-auto px-8 py-4 rounded-2xl font-black text-lg bg-sky-600 hover:bg-sky-700 shadow-md min-h-[56px]"
                        id="voice-record-btn"
                      >
                        {isProcessingVoice
                          ? isHindi
                            ? '⏳ आवाज़ प्रोसेस हो रही है...'
                            : '⏳ Processing Audio...'
                          : isHindi
                          ? '🎤 बोलें (Speak)'
                          : '🎤 Speak'}
                      </Button>
                    ) : (
                      <Button
                        type="button"
                        variant="danger"
                        size="xl"
                        onClick={handleStopRecording}
                        leftIcon={<Square className="w-5 h-5 text-white fill-white" />}
                        className="w-full sm:w-auto px-8 py-4 rounded-2xl font-black text-lg bg-rose-600 hover:bg-rose-700 shadow-lg animate-pulse min-h-[56px]"
                        id="voice-stop-btn"
                      >
                        {isHindi ? '⏹ रोकें एवं भेजें (Stop & Send)' : '⏹ Stop & Send'}
                      </Button>
                    )}
                  </div>

                  {/* Live Transcript Display Card */}
                  {lastTranscript && (
                    <div className="p-3.5 rounded-xl bg-white border border-sky-200 text-xs text-slate-800 shadow-2xs space-y-1 animate-in fade-in" id="voice-transcript-card">
                      <span className="font-bold text-[10px] uppercase tracking-wider text-slate-400 block">
                        {isHindi ? 'आपने कहा (You said):' : 'You said:'}
                      </span>
                      <p className="text-sm font-semibold text-sky-950 italic" id="voice-transcript-text">
                        "{lastTranscript}"
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Processing Spinner */}
              {(isSubmitting || isProcessingVoice) && (
                <div className="p-4 rounded-2xl bg-sky-50 border border-sky-200 flex items-center gap-3 animate-pulse" id="processing-indicator">
                  <div className="w-5 h-5 border-2 border-sky-600 border-t-transparent rounded-full animate-spin shrink-0" />
                  <span className="text-sm font-bold text-sky-900">
                    {isProcessingVoice
                      ? isHindi
                        ? 'आवाज़ का विश्लेषण हो रहा है (Processing audio)...'
                        : 'Transcribing speech & analyzing symptoms...'
                      : isHindi
                      ? 'कृपया प्रतीक्षा करें (Please wait)...'
                      : 'Analyzing response. Please wait...'}
                  </span>
                </div>
              )}

              {/* Quick Answer Suggestion Buttons */}
              <div className="space-y-1.5 pt-1">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                  <span>{isHindi ? 'त्वरित उदाहरण (टैप करें)' : 'Quick Examples (Tap to use)'}</span>
                  <span className="text-sky-600">⚡ Easy Tap</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {demoQuickResponses.map((suggestion, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSendResponse(suggestion)}
                      disabled={isSubmitting || isProcessingVoice || isRecording}
                      className="px-3.5 py-2 bg-slate-50 hover:bg-sky-50 hover:border-sky-300 border border-slate-200 text-slate-800 hover:text-sky-900 rounded-xl text-xs font-semibold transition-all cursor-pointer disabled:opacity-50 text-left active:scale-95 shadow-2xs"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>

              {/* Patient Text Answer Input Area (Seamless Fallback) */}
              <div className="space-y-3 pt-2">
                <label
                  htmlFor="patient-answer-input"
                  className="block text-xs font-bold uppercase tracking-wider text-slate-700"
                >
                  {isHindi ? 'या यहाँ लिखें (Or Type Your Answer):' : 'Or Type Your Answer:'}
                </label>
                <div className="relative">
                  <input
                    id="patient-answer-input"
                    ref={inputRef}
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !isSubmitting && !isProcessingVoice && inputText.trim()) {
                        handleSendResponse();
                      }
                    }}
                    placeholder={
                      isHindi
                        ? 'यहाँ अपना उत्तर लिखें (उदा. 3 दिन से दर्द है)...'
                        : 'Type your symptoms or answer here...'
                    }
                    disabled={isSubmitting || isProcessingVoice || isRecording}
                    className="w-full px-5 py-4 rounded-2xl border-2 border-slate-300 focus:border-sky-600 focus:ring-4 focus:ring-sky-100 text-base sm:text-lg text-slate-900 font-medium placeholder-slate-400 bg-white transition-all shadow-inner"
                  />
                </div>

                {/* Submit / Continue Button */}
                <div className="flex items-center gap-3 pt-2">
                  <Button
                    variant="primary"
                    size="xl"
                    onClick={() => handleSendResponse()}
                    disabled={!inputText.trim() || isSubmitting || isProcessingVoice || isRecording}
                    rightIcon={<ArrowRight className="w-6 h-6" />}
                    className="w-full text-lg font-bold shadow-md rounded-2xl py-4 min-h-[56px]"
                    id="submit-answer-button"
                  >
                    {isSubmitting || isProcessingVoice
                      ? isHindi
                        ? 'प्रतीक्षा करें...'
                        : 'Please wait...'
                      : isHindi
                      ? 'आगे बढ़ें / भेजें (Continue)'
                      : 'Continue'}
                  </Button>
                </div>
              </div>
            </div>

            {/* Right 1 Col: Live Extracted Structured Data */}
            <div className="md:col-span-1 space-y-4">
              <ExtractedInfo data={extractedData} language={language} />

              <div className="p-4 rounded-2xl bg-white border border-slate-200 text-xs text-slate-600 space-y-2 shadow-xs">
                <div className="flex items-center gap-1.5 font-bold text-slate-800">
                  <HelpCircle className="w-4 h-4 text-sky-600" />
                  <span>{isHindi ? 'मदद एवं वॉइस निर्देश' : 'Voice & Text Instructions'}</span>
                </div>
                <p className="leading-relaxed text-[12px]">
                  {isHindi
                    ? 'आप बोलकर या लिखकर अपनी भाषा में बता सकते हैं। वॉइस मोड चालू करने पर सवाल बोलकर भी सुनाया जाएगा।'
                    : 'You can speak using the microphone or type your symptoms. When Voice Mode is ON, questions are also spoken aloud.'}
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-3 bg-white text-center text-xs text-slate-500">
        Medisaarthi • AI Pre-Consultation Voice & Text Assistant
      </footer>
    </div>
  );
}
