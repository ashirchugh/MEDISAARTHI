'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Language } from '@/types';
import { PatientHeader } from '@/components/patient/PatientHeader';
import { LanguageSelector } from '@/components/patient/LanguageSelector';
import { Button } from '@/components/ui/Button';
import { ArrowRight, Languages } from 'lucide-react';

export default function LanguageSelectionPage() {
  const router = useRouter();
  const [selectedLanguage, setSelectedLanguage] = useState<Language>('hi');

  useEffect(() => {
    try {
      const stored = localStorage.getItem('medisaarthi_selected_lang');
      if (stored === 'en' || stored === 'hi') {
        setSelectedLanguage(stored);
      }
    } catch {}
  }, []);

  const handleContinue = () => {
    try {
      localStorage.setItem('medisaarthi_selected_lang', selectedLanguage);
    } catch {}
    router.push('/patient/consent');
  };

  const isHindi = selectedLanguage === 'hi';

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between text-slate-900">
      <PatientHeader currentStep={2} totalSteps={4} stepName="Language" />

      <main className="flex-1 max-w-2xl mx-auto px-4 sm:px-6 py-8 sm:py-12 flex flex-col justify-center space-y-8 w-full">
        {/* Title & Prompt */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-100 text-sky-800 text-xs font-bold mb-1">
            <Languages className="w-3.5 h-3.5 text-sky-600" />
            <span>भाषा चयन / Language Selection</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            अपनी भाषा चुनें / Choose your language
          </h1>
          <p className="text-base text-slate-600 max-w-md mx-auto">
            {isHindi
              ? 'जिस भाषा में आप बातचीत करना चाहते हैं, उस पर टैप करें।'
              : 'Select the language you feel most comfortable reading and speaking.'}
          </p>
        </div>

        {/* Big Language Selection Cards */}
        <LanguageSelector
          selected={selectedLanguage}
          onSelect={(lang) => setSelectedLanguage(lang)}
        />

        {/* Continue Button */}
        <div className="pt-4 max-w-md mx-auto w-full">
          <Button
            variant="primary"
            size="xl"
            onClick={handleContinue}
            rightIcon={<ArrowRight className="w-5 h-5" />}
            className="w-full text-lg font-bold shadow-md rounded-2xl py-4 min-h-[56px]"
            id="continue-button"
          >
            {selectedLanguage === 'hi' ? 'आगे बढ़ें (Continue)' : 'Continue'}
          </Button>
        </div>
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        Selected Language: <strong>{selectedLanguage === 'hi' ? 'हिंदी (Hindi)' : 'English'}</strong>
      </footer>
    </div>
  );
}
