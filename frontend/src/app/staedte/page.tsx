'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FehlerAnzeige } from '@/components/ui/fehler-anzeige';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { Skeleton } from '@/components/ui/skeleton';
import { BalkenDiagramm } from '@/components/charts/balken-diagramm';
import { useApi } from '@/hooks/use-api';
import type { StadtKennzahl } from '@/lib/api';

export default function StaedteSeite() {
  const staedte = useApi<StadtKennzahl[]>('/cities?limit=20');

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Staedte</h1>
        <p className="text-sm text-muted-foreground">Regionale Verteilung der aktuellen Anzeigen.</p>
      </header>
      <Card>
        <CardHeader>
          <CardTitle>Top 20 Staedte</CardTitle>
        </CardHeader>
        <CardContent>
          {staedte.isLoading && <Skeleton className="h-96 w-full" />}
          {staedte.error && <FehlerAnzeige meldung="Staedte konnten nicht geladen werden." />}
          {!staedte.isLoading && !staedte.error && (!staedte.data || staedte.data.length === 0) && (
            <LeererZustand titel="Noch keine Stadt-Daten vorhanden." />
          )}
          {!staedte.isLoading && !staedte.error && staedte.data && staedte.data.length > 0 && (
            <div className="h-96">
              <BalkenDiagramm
                daten={staedte.data.map((eintrag) => ({
                  beschriftung: eintrag.stadt,
                  wert: eintrag.anzahl_jobs,
                }))}
                hoehe={384}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
