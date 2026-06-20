'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FehlerAnzeige } from '@/components/ui/fehler-anzeige';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { Skeleton } from '@/components/ui/skeleton';
import { LinienDiagramm } from '@/components/charts/linien-diagramm';
import { VerteilungsDiagramm } from '@/components/charts/verteilungs-diagramm';
import { useApi } from '@/hooks/use-api';
import type { GehaltsverteilungEintrag, ZeitreihePunkt } from '@/lib/api';

type Gruppierung = 'kategorie' | 'stadt' | 'bundesland';

export default function TrendsSeite() {
  const [gruppierung, setGruppierung] = useState<Gruppierung>('kategorie');
  const zeitreihe = useApi<ZeitreihePunkt[]>('/trends/zeitreihe?tage=60');
  const verteilung = useApi<GehaltsverteilungEintrag[]>(`/trends/gehaltsverteilung?gruppierung=${gruppierung}`);

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Trends</h1>
        <p className="text-sm text-muted-foreground">
          Entwicklung der Anzeigen ueber die Zeit und Verteilung der Gehaelter.
        </p>
      </header>
      <Card>
        <CardHeader>
          <CardTitle>Zeitreihe (60 Tage)</CardTitle>
        </CardHeader>
        <CardContent>
          {zeitreihe.isLoading && <Skeleton className="h-80 w-full" />}
          {zeitreihe.error && <FehlerAnzeige meldung="Zeitreihe konnte nicht geladen werden." />}
          {!zeitreihe.isLoading && !zeitreihe.error && (!zeitreihe.data || zeitreihe.data.length === 0) && (
            <LeererZustand titel="Noch keine Trenddaten vorhanden." />
          )}
          {!zeitreihe.isLoading && !zeitreihe.error && zeitreihe.data && zeitreihe.data.length > 0 && (
            <div className="h-80">
              <LinienDiagramm daten={zeitreihe.data} hoehe={320} />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Gehaltsverteilung</CardTitle>
          <div className="flex gap-2 pt-2">
            {(['kategorie', 'stadt', 'bundesland'] as const).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setGruppierung(option)}
                className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                  gruppierung === option ? 'bg-foreground text-background' : 'bg-card text-muted-foreground hover:text-foreground'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {verteilung.isLoading && <Skeleton className="h-96 w-full" />}
          {verteilung.error && <FehlerAnzeige meldung="Verteilung konnte nicht geladen werden." />}
          {!verteilung.isLoading && !verteilung.error && (!verteilung.data || verteilung.data.length === 0) && (
            <LeererZustand titel="Keine Gehaltsdaten verfuegbar." />
          )}
          {!verteilung.isLoading && !verteilung.error && verteilung.data && verteilung.data.length > 0 && (
            <div className="h-96">
              <VerteilungsDiagramm daten={verteilung.data} hoehe={384} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
