'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Patient, Language } from '@/types';
import { INITIAL_PATIENTS } from '@/lib/mock-data';
import { PatientHeader } from '@/components/patient/PatientHeader';
import { PatientIdentification } from '@/components/patient/PatientIdentification';
import { Button } from '@/components/ui/Button';
import { ArrowRight, UserCheck } from 'lucide-react';

export default function PatientIdentifyPage() {
  const router = useRouter();
  const [selectedPatient, setSelectedPatient] = useState<Patient>(INITIAL_PATIENTS[0]);
  const [language, setLanguage] = useState<Language>('hi');

  useEffect(() => {
    try {
      const storedLang = localStorage.getItem('medisaarthi_selected_lang');
      if (storedLang === 'en' || storedLang === 'hi') {
        setLanguage(storedLang);
      }
    } catch {}
  }, []);

  const handleContinue = () => {
    try {
      localStorage.setItem('medisaarthi_current_patient_id', selectedPatient.patient_id);
    } catch {}
    router.push('/patient/language');
  };

  const isHindi = language === 'hi';

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between text-slate-900">
      <PatientHeader currentStep={1} totalSteps={4} stepName="Identification" />

      <main className="flex-1 max-w-2xl mx-auto px-4 sm:px-6 py-8 sm:py-12 flex flex-col justify-center space-y-6 w-full">
        {/* Title */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-100 text-sky-800 text-xs font-bold mb-1">
            <UserCheck className="w-3.5 h-3.5 text-sky-600" />
            <span>{isHindi ? 'मरीज की पहचान' : 'Patient Identification'}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {isHindi ? 'अपनी जानकारी चुनें या दर्ज करें' : 'Confirm your details'}
          </h1>
          <p className="text-base text-slate-600 max-w-md mx-auto">
            {isHindi
              ? 'डेमो मरीज (P1001 — राजेश कुमार) चुनें या अपनी मरीज आईडी दर्ज करें।'
              : 'Select demo patient (P1001 — Rajesh Kumar) or enter your patient ID.'}
          </p>
        </div>

        {/* Identification Form & Demo Switcher */}
        <PatientIdentification
          initialPatient={selectedPatient}
          onPatientSelected={(p) => setSelectedPatient(p)}
          language={language}
        />

        {/* Continue CTA */}
        <div className="pt-2 max-w-md mx-auto w-full">
          <Button
            variant="primary"
            size="xl"
            onClick={handleContinue}
            rightIcon={<ArrowRight className="w-5 h-5" />}
            className="w-full text-lg font-bold shadow-md rounded-2xl py-4 min-h-[56px]"
            id="continue-button"
          >
            {isHindi ? 'आगे बढ़ें (Continue)' : 'Continue'}
          </Button>
        </div>
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        Selected Profile: <strong>{selectedPatient.name}</strong> ({selectedPatient.patient_id})
      </footer>
    </div>
  );
}
