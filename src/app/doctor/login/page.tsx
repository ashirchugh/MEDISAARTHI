'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { HeartPulse, Stethoscope, Lock, Mail, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { CURRENT_DOCTOR } from '@/lib/mock-data';

export default function DoctorLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('dr.sharma@apexhealth.org');
  const [password, setPassword] = useState('••••••••••••');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      router.push('/doctor');
    }, 400);
  };

  const handleDemoLogin = () => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      router.push('/doctor');
    }, 300);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-between text-slate-100 selection:bg-sky-500 selection:text-white">
      {/* Top Brand Bar */}
      <header className="p-6">
        <Link href="/" className="inline-flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-2xl bg-sky-500 text-slate-950 flex items-center justify-center font-bold shadow-md">
            <HeartPulse className="w-6 h-6" />
          </div>
          <div>
            <span className="font-bold text-lg text-white tracking-tight leading-none block">
              MEDISAARTHI
            </span>
            <span className="text-[11px] text-sky-400 font-semibold tracking-wider uppercase leading-none">
              Physician Portal
            </span>
          </div>
        </Link>
      </header>

      {/* Main Login Card */}
      <main className="max-w-md w-full mx-auto px-4 py-8 space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-sky-400 text-xs font-semibold">
            <Stethoscope className="w-3.5 h-3.5" />
            <span>Authorized Clinical Access</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Physician Sign-in
          </h1>
          <p className="text-xs text-slate-400">
            Apex Multi-Speciality Hospital • OPD Triage & Verification
          </p>
        </div>

        <div className="bg-slate-800/80 border border-slate-700 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-md space-y-5">
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5">
                Hospital Email ID
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="doctor@hospital.org"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5">
                Staff Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              className="w-full font-bold text-sm rounded-xl mt-2"
            >
              Sign In to Dashboard
            </Button>
          </form>

          <div className="relative flex items-center justify-center py-2">
            <div className="border-t border-slate-700 w-full" />
            <span className="bg-slate-800 px-3 text-[11px] text-slate-400 uppercase font-bold tracking-wider absolute">
              Quick Demo Login
            </span>
          </div>

          {/* Quick Demo Login Option */}
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={isLoading}
            className="w-full p-3.5 rounded-2xl bg-sky-600/20 hover:bg-sky-600/30 border border-sky-500/40 text-sky-300 hover:text-white transition-all text-left flex items-center justify-between group cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-sky-500 text-slate-950 font-bold flex items-center justify-center text-xs">
                {CURRENT_DOCTOR.avatar}
              </div>
              <div>
                <div className="font-bold text-xs text-white group-hover:text-sky-200">
                  {CURRENT_DOCTOR.name}
                </div>
                <div className="text-[11px] text-slate-400">
                  {CURRENT_DOCTOR.designation}
                </div>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-sky-400 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>

        <div className="text-center text-xs text-slate-500 flex items-center justify-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-sky-500" />
          <span>HIPAA & Hospital Clinical Data Compliance Standard</span>
        </div>
      </main>

      <footer className="p-4 text-center text-xs text-slate-600">
        Medisaarthi Clinical Dashboard • Round 1 Prototype
      </footer>
    </div>
  );
}
