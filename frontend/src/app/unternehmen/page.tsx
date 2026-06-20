'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FehlerAnzeige } from '@/components/ui/fehler-anzeige';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { Skeleton } from '@/components/ui/skeleton';
import { useApi } from '@/hooks/use-api';
import type { UnternehmensKennzahl } from '@/lib/api';
import { formatGehalt, formatZahl } from '@/lib/utils';

export default function UnternehmenSeite() {
  const unternehmen = useApi<UnternehmensKennzahl[]>('/companies?limit=50');

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Unternehmen</h1>
        <p className="text-sm text-muted-foreground">
          Unternehmen mit den meisten aktuellen Anzeigen im deutschen Markt.
        </p>
      </header>
      <Card>
        <CardHeader>
          <CardTitle>Rangliste</CardTitle>
        </CardHeader>
        <CardContent>
          {unternehmen.isLoading && <Skeleton className="h-96 w-full" />}
          {unternehmen.error && <FehlerAnzeige meldung="Unternehmen konnten nicht geladen werden." />}
          {!unternehmen.isLoading && !unternehmen.error && (!unternehmen.data || unternehmen.data.length === 0) && (
            <LeererZustand titel="Noch keine Unternehmensdaten vorhanden." />
          )}
          {!unternehmen.isLoading && !unternehmen.error && unternehmen.data && unternehmen.data.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full table-auto text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="px-3 py-2">Unternehmen</th>
                    <th className="px-3 py-2 text-right">Anzeigen</th>
                    <th className="px-3 py-2 text-right">Mittleres Gehalt</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {unternehmen.data.map((eintrag) => (
                    <tr key={eintrag.unternehmen}>
                      <td className="px-3 py-2">{eintrag.unternehmen}</td>
                      <td className="kennzahl px-3 py-2 text-right">{formatZahl(eintrag.anzahl_jobs)}</td>
                      <td className="kennzahl px-3 py-2 text-right">{formatGehalt(eintrag.gehalt_mittel)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
