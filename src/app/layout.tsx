import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Medisaarthi | AI-Powered Pre-Consultation Intelligence Platform',
  description:
    'Bridging patient registration and doctor consultation with conversational AI symptom intake and clinical summary preparation.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans bg-slate-50 text-slate-900 selection:bg-sky-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
