import React, { useState, useEffect } from 'react';
import { Mic, Square, Volume2, Sparkles } from 'lucide-react';

interface VoiceRecorderProps {
  onTranscribed: (text: string) => void;
  language?: 'hi' | 'en';
  isProcessing?: boolean;
  activeQuestionIndex?: number;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onTranscribed,
  language = 'hi',
  isProcessing = false,
  activeQuestionIndex = 0,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);

  const isHindi = language === 'hi';

  // Demo audio transcriptions mapped to the question flow for Rajesh Kumar / demo patients
  const sampleTranscriptionsHi = [
    'मुझे तीन दिन से सीने में दर्द हो रहा है और भारीपन लगता है।',
    'लगभग 7 आउट ऑफ 10. चलने-फिरने पर बढ़ जाता है।',
    'हाँ, सांस लेने में तकलीफ होती है और पसीना भी आ रहा है।',
    'हाँ, 2021 से बीपी की दवा (Amlodipine) और 2023 से शुगर (Metformin) ले रहे हैं।',
    'नहीं, किसी दवा से कोई ज्ञात एलर्जी नहीं है।',
  ];

  const sampleTranscriptionsEn = [
    'I have been having chest pain and tightness for the past 3 days.',
    'It is about 7 out of 10. Worsens when I walk or climb stairs.',
    'Yes, I have slight breathlessness and mild sweating.',
    'Yes, I take Amlodipine 5mg for high BP since 2021 and Metformin 500mg for Diabetes.',
    'No known drug allergies.',
  ];

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setRecordSeconds(0);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const startRecording = () => {
    if (isProcessing) return;
    setIsRecording(true);
    setRecordSeconds(0);
  };

  const stopRecording = () => {
    setIsRecording(false);
    // Simulate smart voice-to-text processing
    setTimeout(() => {
      const pool = isHindi ? sampleTranscriptionsHi : sampleTranscriptionsEn;
      const text = pool[activeQuestionIndex % pool.length] || (isHindi ? 'मुझे सीने में दर्द है।' : 'I have chest pain.');
      onTranscribed(text);
    }, 600);
  };

  return (
    <div className="flex flex-col items-center justify-center">
      {isRecording ? (
        <div className="flex flex-col items-center gap-3 p-4 bg-rose-50 border-2 border-rose-300 rounded-2xl w-full animate-in fade-in">
          <div className="flex items-center gap-3">
            {/* Animated Waveform */}
            <div className="flex items-center gap-1.5 h-8 px-2 bg-rose-100/80 rounded-lg">
              <span className="w-1.5 bg-rose-600 rounded-full animate-wave-1 h-3" />
              <span className="w-1.5 bg-rose-600 rounded-full animate-wave-2 h-5" />
              <span className="w-1.5 bg-rose-600 rounded-full animate-wave-3 h-7" />
              <span className="w-1.5 bg-rose-600 rounded-full animate-wave-4 h-4" />
              <span className="w-1.5 bg-rose-600 rounded-full animate-wave-5 h-6" />
              <span className="w-1.5 bg-rose-600 rounded-full animate-wave-6 h-3" />
            </div>

            <div className="text-left">
              <div className="flex items-center gap-1.5 text-xs font-bold text-rose-700">
                <span className="w-2 h-2 rounded-full bg-rose-600 animate-ping" />
                <span>{isHindi ? 'सुन रहे हैं...' : 'Listening...'} ({recordSeconds}s)</span>
              </div>
              <p className="text-[11px] text-rose-600 font-medium">
                {isHindi ? 'कृपया अपने लक्षण बोलें' : 'Speak your symptoms clearly'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={stopRecording}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors cursor-pointer"
            aria-label="Stop recording and transcribe speech"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>{isHindi ? 'बोलना समाप्त करें' : 'Done Speaking'}</span>
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={startRecording}
          disabled={isProcessing}
          className="group relative flex items-center justify-center gap-2 p-3 sm:px-5 sm:py-3.5 bg-gradient-to-b from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white rounded-2xl shadow-md hover:shadow-lg transition-all transform active:scale-95 disabled:opacity-50 cursor-pointer min-h-[48px]"
          aria-label={isHindi ? 'माइक दबाकर बोलें' : 'Click microphone to speak your response'}
        >
          <div className="relative">
            <Mic className="w-5 h-5 text-white transition-transform group-hover:scale-110" />
            <span className="absolute -top-1 -right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-200 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
            </span>
          </div>
          <span className="hidden sm:inline font-bold text-sm tracking-wide">
            {isHindi ? 'बोलकर बताएं' : 'Voice Input'}
          </span>
        </button>
      )}
    </div>
  );
};
