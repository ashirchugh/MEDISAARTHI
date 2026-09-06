import React from 'react';
import { DoctorSidebar } from '@/components/doctor/Sidebar';

export default function DoctorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-100 flex font-sans">
      {/* Fixed/Sticky Left Sidebar on desktop */}
      <div className="hidden md:block">
        <DoctorSidebar />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {children}
      </div>
    </div>
  );
}
