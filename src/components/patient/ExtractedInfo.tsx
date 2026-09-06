import React, { useState } from 'react';
import { ExtractedSymptomData } from '@/types';
import { Sparkles, ChevronDown, ChevronUp, Activity, Clock, Flame, AlertCircle } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

interface ExtractedInfoProps {
  data: ExtractedSymptomData;
  language?: 'hi' | 'en';
}

export const ExtractedInfo: React.FC<ExtractedInfoProps> = ({
  data,
  language = 'hi',
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isHindi = language === 'hi';

  const hasAnyData =
    Boolean(data.chief_complaint) ||
    Boolean(data.duration) ||
    Boolean(data.severity) ||
    data.associated_symptoms.length > 0;

  return (
    <aside className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all">
      {/* Header / Mobile Toggle */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 bg-slate-50/80 border-b border-slate-100 text-left cursor-pointer md:cursor-default"
      >
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-900 block">
              {isHindi ? 'संकलित जानकारी' : 'Information Collected'}
            </span>
            <span className="text-[11px] text-slate-500 block">
              {isHindi ? 'डॉक्टर के लिए लाइव समरी' : 'Live summary for doctor'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={hasAnyData ? 'success' : 'neutral'} size="sm">
            {hasAnyData ? (isHindi ? 'लाइव अपडेट' : 'Active Sync') : (isHindi ? 'प्रतीक्षा' : 'Awaiting')}
          </Badge>
          <div className="md:hidden text-slate-400">
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>
      </button>

      {/* Content Area - Always open on desktop, collapsible on mobile */}
      <div className={`p-4 space-y-4 ${isExpanded ? 'block' : 'hidden md:block'}`}>
        {!hasAnyData ? (
          <div className="text-center py-6 text-slate-400 text-xs">
            <Activity className="w-8 h-8 mx-auto mb-2 opacity-40 animate-pulse" />
            <p>
              {isHindi
                ? 'जैसे ही आप उत्तर देंगे, यहाँ जानकारी स्वतः संकलित होगी।'
                : 'Extracted symptoms will appear here in real-time as you speak or answer.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3.5 text-xs">
            {/* Chief Complaint */}
            {data.chief_complaint && (
              <div className="p-2.5 rounded-xl bg-sky-50/70 border border-sky-100">
                <span className="text-[10px] font-bold uppercase tracking-wider text-sky-700 block mb-0.5">
                  {isHindi ? 'मुख्य समस्या (Chief Concern)' : 'Chief Concern'}
                </span>
                <span className="font-semibold text-sky-950 text-sm block">
                  {data.chief_complaint}
                </span>
              </div>
            )}

            {/* Duration */}
            {data.duration && (
              <div className="flex items-start gap-2.5 p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <Clock className="w-4 h-4 text-slate-500 mt-0.5" />
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                    {isHindi ? 'अवधि (Duration)' : 'Duration'}
                  </span>
                  <span className="font-medium text-slate-800">
                    {data.duration}
                  </span>
                </div>
              </div>
            )}

            {/* Severity */}
            {data.severity && (
              <div className="flex items-start gap-2.5 p-2.5 rounded-xl bg-amber-50/60 border border-amber-100">
                <Flame className="w-4 h-4 text-amber-600 mt-0.5" />
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-amber-800 block">
                    {isHindi ? 'तीव्रता (Severity)' : 'Severity Scale'}
                  </span>
                  <span className="font-bold text-amber-950">
                    {data.severity}
                  </span>
                </div>
              </div>
            )}

            {/* Associated Symptoms */}
            {data.associated_symptoms.length > 0 && (
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 space-y-1.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                  {isHindi ? 'अन्य लक्षण (Associated Symptoms)' : 'Associated Symptoms'}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {data.associated_symptoms.map((sym, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-800 font-medium text-[11px]"
                    >
                      {sym}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Verification Note */}
        <div className="pt-2 border-t border-slate-100 flex items-center gap-1.5 text-[10px] text-slate-400">
          <AlertCircle className="w-3 h-3 text-slate-400 shrink-0" />
          <span>
            {isHindi
              ? 'यह केवल जानकारी है, निदान नहीं। डॉक्टर द्वारा सत्यापित की जाएगी।'
              : 'Pre-consultation data requires physician verification.'}
          </span>
        </div>
      </div>
    </aside>
  );
};
