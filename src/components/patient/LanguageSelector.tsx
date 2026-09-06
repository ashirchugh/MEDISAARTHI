import React from 'react';
import { Language } from '@/types';
import { CheckCircle2, Globe } from 'lucide-react';

interface LanguageSelectorProps {
  selected: Language;
  onSelect: (lang: Language) => void;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  selected,
  onSelect,
}) => {
  const languages: { id: Language; nativeName: string; englishName: string; flag: string; desc: string }[] = [
    {
      id: 'hi',
      nativeName: 'हिंदी',
      englishName: 'Hindi',
      flag: '🇮🇳',
      desc: 'अपनी भाषा में आसानी से बात करें',
    },
    {
      id: 'en',
      nativeName: 'English',
      englishName: 'English',
      flag: '🇬🇧',
      desc: 'Continue interview in English',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
      {languages.map((lang) => {
        const isSelected = selected === lang.id;
        return (
          <button
            key={lang.id}
            type="button"
            onClick={() => onSelect(lang.id)}
            className={`relative flex flex-col p-6 text-left rounded-2xl border-2 transition-all duration-200 cursor-pointer ${
              isSelected
                ? 'border-sky-600 bg-sky-50/50 shadow-md ring-2 ring-sky-500/20'
                : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/70 shadow-xs'
            }`}
            aria-pressed={isSelected}
          >
            <div className="flex items-start justify-between w-full mb-3">
              <span className="text-4xl" role="img" aria-label={lang.englishName}>
                {lang.flag}
              </span>
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center transition-colors ${
                  isSelected ? 'text-sky-600' : 'text-slate-300'
                }`}
              >
                <CheckCircle2
                  className={`w-6 h-6 ${isSelected ? 'fill-sky-100 stroke-sky-600' : 'stroke-slate-300'}`}
                />
              </div>
            </div>

            <div className="mt-1">
              <span className="text-2xl font-bold text-slate-900 block tracking-tight">
                {lang.nativeName}
              </span>
              <span className="text-sm font-medium text-slate-500 block mt-0.5">
                {lang.englishName}
              </span>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-1.5 text-xs text-slate-600">
              <Globe className="w-3.5 h-3.5 text-slate-400" />
              <span>{lang.desc}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
};
