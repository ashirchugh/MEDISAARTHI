'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Patient, Language, DoctorSummaryResponse } from '@/types';
import { getPatient, getDoctorSummary } from '@/services/api';
import { INITIAL_PATIENTS } from '@/lib/mock-data';
import { PatientHeader } from '@/components/patient/PatientHeader';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  CheckCircle2,
  Clock,
  ArrowRight,
  FileCheck,
  User,
  ShieldCheck,
} from 'lucide-react';

export default function PatientCompletedPage() {
  const [patient, setPatient] = useState<Patient>(INITIAL_PATIENTS[0]);
  const [summary, setSummary] = useState<DoctorSummaryResponse | null>(null);
  const [language, setLanguage] = useState<Language>('hi');

  useEffect(() => {
    const load = async () => {
      let currentId = 'P1001';
      let currentLang: Language = 'hi';
      try {
        const storedId = localStorage.getItem('medisaarthi_current_patient_id');
        const storedLang = localStorage.getItem('medisaarthi_selected_lang');
        if (storedId) currentId = storedId;
        if (storedLang === 'en' || storedLang === 'hi') currentLang = storedLang;
      } catch {}

      setLanguage(currentLang);
      const p = (await getPatient(currentId)) || INITIAL_PATIENTS[0];
      setPatient(p);

      try {
        const s = await getDoctorSummary(currentId);
        if (s) setSummary(s);
      } catch {}
    };

    load();
  }, []);

  const isHindi = language === 'hi';

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between text-slate-900">
      <PatientHeader showDoctorPortalLink={false} />

      <main className="flex-1 max-w-2xl mx-auto px-4 sm:px-6 py-8 sm:py-12 flex flex-col justify-center space-y-6 w-full text-center">
        {/* Large Success Icon */}
        <div className="relative mx-auto">
          <div className="w-24 h-24 rounded-3xl bg-emerald-600 text-white flex items-center justify-center shadow-xl shadow-emerald-600/25 ring-8 ring-emerald-100">
            <CheckCircle2 className="w-12 h-12" />
          </div>
        </div>

        {/* Completion Heading */}
        <div className="space-y-3">
          <Badge variant="success" size="md" className="px-3.5 py-1 text-xs font-bold uppercase tracking-wider">
            {isHindi ? 'इंटरव्यू पूरा हुआ • Interview Completed' : 'Interview Completed'}
          </Badge>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            {isHindi ? 'धन्यवाद।' : 'Thank you.'}
          </h1>

          <p className="text-lg sm:text-xl text-slate-700 font-medium max-w-lg mx-auto leading-relaxed">
            {isHindi
              ? 'आपकी जानकारी सुरक्षित रूप से दर्ज कर ली गई है और डॉक्टर की समीक्षा के लिए उपलब्ध रहेगी।'
              : 'Your information has been recorded and will be available to the doctor for review.'}
          </p>
        </div>

        {/* Confirmation Card */}
        <div className="bg-white rounded-3xl border border-slate-200 shadow-md p-6 sm:p-8 text-left space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2.5">
              <User className="w-5 h-5 text-sky-600" />
              <span className="font-bold text-sm text-slate-900 uppercase tracking-wider">
                {patient.name} ({patient.patient_id})
              </span>
            </div>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
              {isHindi ? 'समीक्षा हेतु तैयार' : 'Ready for Review'}
            </span>
          </div>

          <div className="space-y-3 text-xs sm:text-sm text-slate-600">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center gap-2.5">
                <FileCheck className="w-5 h-5 text-teal-600 shrink-0" />
                <span className="font-semibold text-slate-800">
                  {isHindi ? 'लक्षण एवं अवधि' : 'Symptoms & Duration'}
                </span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center gap-2.5">
                <FileCheck className="w-5 h-5 text-teal-600 shrink-0" />
                <span className="font-semibold text-slate-800">
                  {isHindi ? 'दर्द की तीव्रता' : 'Severity Details'}
                </span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center gap-2.5">
                <FileCheck className="w-5 h-5 text-teal-600 shrink-0" />
                <span className="font-semibold text-slate-800">
                  {isHindi ? 'पुरानी बीमारियां' : 'Past Medical History'}
                </span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center gap-2.5">
                <FileCheck className="w-5 h-5 text-teal-600 shrink-0" />
                <span className="font-semibold text-slate-800">
                  {isHindi ? 'दवाइयां एवं एलर्जी' : 'Medications & Allergies'}
                </span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 text-xs text-slate-500 flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400 shrink-0" />
              <span>
                {isHindi
                  ? 'कृपया प्रतीक्षालय में प्रतीक्षा करें। आपके डॉक्टर परामर्श के दौरान आपकी जानकारी की समीक्षा करेंगे।'
                  : 'Please wait in the consultation waiting area. Your doctor will review this summary before your turn.'}
              </span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-2 max-w-md mx-auto w-full">
          <Link href="/patient" className="w-full">
            <Button
              variant="primary"
              size="xl"
              className="w-full text-lg font-bold rounded-2xl py-4 shadow-md min-h-[56px]"
              id="finish-home-button"
            >
              {isHindi ? 'समाप्त करें (Finish)' : 'Finish'}
            </Button>
          </Link>
        </div>
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        Medisaarthi • AI-Assisted Clinical Pre-Consultation Intelligence
      </footer>
    </div>
  );
}
