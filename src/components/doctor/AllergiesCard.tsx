import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { ShieldAlert, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

interface AllergiesCardProps {
  allergies: string[];
}

export const AllergiesCard: React.FC<AllergiesCardProps> = ({ allergies }) => {
  const hasKnownAllergies =
    allergies.length > 0 &&
    !allergies.some((a) => a.toLowerCase().includes('no known') || a.toLowerCase().includes('nkda'));

  return (
    <Card className={`h-full ${hasKnownAllergies ? 'border-rose-300 bg-rose-50/20' : ''}`}>
      <CardHeader>
        <CardTitle className="text-sm font-bold uppercase tracking-wider text-slate-800">
          <ShieldAlert
            className={`w-4 h-4 ${hasKnownAllergies ? 'text-rose-600' : 'text-slate-500'}`}
          />
          <span>Known Drug & Substance Allergies</span>
        </CardTitle>
        <Badge variant={hasKnownAllergies ? 'danger' : 'success'} size="sm">
          {hasKnownAllergies ? 'Allergy Warning' : 'NKDA'}
        </Badge>
      </CardHeader>
      <CardContent>
        {hasKnownAllergies ? (
          <div className="space-y-2.5">
            {allergies.map((allergy, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-950 flex items-start gap-3"
              >
                <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
                <div>
                  <span className="font-bold text-sm block text-rose-900">{allergy}</span>
                  <span className="text-xs text-rose-700 block mt-0.5">
                    Avoid cross-reactive compounds in prescription plan.
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200/80 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <div>
              <span className="font-bold text-sm text-emerald-950 block">
                No Known Drug Allergies (NKDA)
              </span>
              <span className="text-xs text-emerald-800/80 block mt-0.5">
                Patient confirms no historical hypersensitivity or adverse reactions.
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
