import React, { useState } from 'react';
import { Patient, Gender } from '@/types';
import { INITIAL_PATIENTS } from '@/lib/mock-data';
import { User, IdCard, Calendar, Users, CheckCircle, Search, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

interface PatientIdentificationProps {
  initialPatient?: Patient;
  onPatientSelected: (patient: Patient) => void;
  language?: 'hi' | 'en';
}

export const PatientIdentification: React.FC<PatientIdentificationProps> = ({
  initialPatient,
  onPatientSelected,
  language = 'hi',
}) => {
  const isHindi = language === 'hi';

  const [patientId, setPatientId] = useState(initialPatient?.patient_id || 'P1001');
  const [name, setName] = useState(initialPatient?.name || 'Rajesh Kumar');
  const [age, setAge] = useState<number | ''>(initialPatient?.age || 48);
  const [gender, setGender] = useState<Gender>(initialPatient?.gender || 'Male');
  const [isConfirmed, setIsConfirmed] = useState(true);

  const handleSelectDemoPatient = (p: Patient) => {
    setPatientId(p.patient_id);
    setName(p.name);
    setAge(p.age);
    setGender(p.gender);
    setIsConfirmed(true);
    onPatientSelected(p);
  };

  const handleLookup = (id: string) => {
    setPatientId(id);
    const found = INITIAL_PATIENTS.find(
      (p) => p.patient_id.toLowerCase() === id.trim().toLowerCase()
    );
    if (found) {
      setName(found.name);
      setAge(found.age);
      setGender(found.gender);
      setIsConfirmed(true);
      onPatientSelected(found);
    } else {
      setIsConfirmed(false);
    }
  };

  const handleManualChange = (
    field: 'name' | 'age' | 'gender',
    val: string | number
  ) => {
    let updatedName = name;
    let updatedAge = age === '' ? 48 : age;
    let updatedGender = gender;

    if (field === 'name') {
      setName(val as string);
      updatedName = val as string;
    } else if (field === 'age') {
      const num = Number(val);
      setAge(num || '');
      updatedAge = num || 48;
    } else if (field === 'gender') {
      setGender(val as Gender);
      updatedGender = val as Gender;
    }

    const currentP: Patient = {
      patient_id: patientId || 'P1001',
      name: updatedName || 'Patient',
      age: typeof updatedAge === 'number' ? updatedAge : 48,
      gender: updatedGender,
      language: language,
    };
    onPatientSelected(currentP);
  };

  return (
    <div className="space-y-6">
      {/* Demo Patient Quick Selectors */}
      <div className="bg-sky-50/60 border border-sky-200/80 rounded-2xl p-4 sm:p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-600" />
            <span className="text-xs font-bold uppercase tracking-wider text-sky-900">
              {isHindi ? 'डेमो मरीज का चयन करें (त्वरित लोड)' : 'Select Demo Patient (One-Click)'}
            </span>
          </div>
          <Badge variant="primary" size="sm">
            {INITIAL_PATIENTS.length} Demo Profiles
          </Badge>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
          {INITIAL_PATIENTS.map((p) => {
            const isSelected = patientId === p.patient_id;
            return (
              <button
                key={p.patient_id}
                type="button"
                onClick={() => handleSelectDemoPatient(p)}
                className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                  isSelected
                    ? 'border-sky-600 bg-white shadow-xs ring-2 ring-sky-500/20'
                    : 'border-sky-200/60 bg-white/70 hover:bg-white text-slate-700'
                }`}
              >
                <div className="font-bold text-xs text-sky-700">{p.patient_id}</div>
                <div className="font-semibold text-xs text-slate-900 truncate mt-0.5">
                  {p.name}
                </div>
                <div className="text-[11px] text-slate-500">
                  {p.age}y • {p.gender}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Identification Form */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Patient ID */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              {isHindi ? 'मरीज आईडी (Patient ID)' : 'Patient ID'}
            </label>
            <div className="relative">
              <IdCard className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={patientId}
                onChange={(e) => handleLookup(e.target.value)}
                placeholder="e.g. P1001"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-slate-900 font-semibold focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          {/* Full Name */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              {isHindi ? 'पूरा नाम (Full Name)' : 'Full Name'}
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={name}
                onChange={(e) => handleManualChange('name', e.target.value)}
                placeholder="Full Name"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-slate-900 font-semibold focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          {/* Age */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              {isHindi ? 'उम्र (Age in Years)' : 'Age (Years)'}
            </label>
            <div className="relative">
              <Calendar className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="number"
                value={age}
                onChange={(e) => handleManualChange('age', e.target.value)}
                placeholder="e.g. 48"
                min={1}
                max={120}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-slate-900 font-semibold focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          {/* Gender */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              {isHindi ? 'लिंग (Gender)' : 'Gender'}
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(['Male', 'Female', 'Other'] as Gender[]).map((g) => {
                const isSelected = gender === g;
                return (
                  <button
                    key={g}
                    type="button"
                    onClick={() => handleManualChange('gender', g)}
                    className={`py-2 px-3 rounded-xl border text-xs font-bold transition-colors cursor-pointer ${
                      isSelected
                        ? 'border-sky-600 bg-sky-50 text-sky-700 ring-1 ring-sky-500'
                        : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {g}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Confirmation Card */}
        {name && (
          <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-sm shadow-2xs">
                <CheckCircle className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-emerald-900">
                  {isHindi ? 'पुष्टि की गई मरीज प्रोफाइल' : 'Verified Registration'}
                </div>
                <div className="text-sm font-bold text-emerald-950">
                  {name} ({age}y • {gender}) • <span className="font-mono">{patientId}</span>
                </div>
              </div>
            </div>
            <Badge variant="success" size="sm">
              {isHindi ? 'सत्यापित' : 'Matched'}
            </Badge>
          </div>
        )}
      </div>
    </div>
  );
};
