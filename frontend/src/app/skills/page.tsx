'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FehlerAnzeige } from '@/components/ui/fehler-anzeige';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { Skeleton } from '@/components/ui/skeleton';
import { BalkenDiagramm } from '@/components/charts/balken-diagramm';
import { useApi } from '@/hooks/use-api';
import type { SkillKennzahl } from '@/lib/api';

export default function SkillsSeite() {
  const skills = useApi<SkillKennzahl[]>('/skills?limit=30');

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Skills</h1>
        <p className="text-sm text-muted-foreground">
          Gefragteste technische Faehigkeiten. Klicken Sie einen Balken an, um die zugehoerigen
          Anzeigen zu sehen.
        </p>
      </header>
      <Card>
        <CardHeader>
          <CardTitle>Top 30 Skills</CardTitle>
        </CardHeader>
        <CardContent>
          {skills.isLoading && <Skeleton className="h-96 w-full" />}
          {skills.error && <FehlerAnzeige meldung="Skills konnten nicht geladen werden." />}
          {!skills.isLoading && !skills.error && (!skills.data || skills.data.length === 0) && (
            <LeererZustand titel="Noch keine Skill-Daten vorhanden." />
          )}
          {!skills.isLoading && !skills.error && skills.data && skills.data.length > 0 && (
            <div className="h-96">
              <BalkenDiagramm
                daten={skills.data.map((eintrag) => ({
                  beschriftung: eintrag.skill,
                  wert: eintrag.anzahl_jobs,
                  ziel: `/anzeigen/?skill=${encodeURIComponent(eintrag.skill)}`,
                }))}
                hoehe={384}
                beschriftungYAchse="Anzeigen"
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
