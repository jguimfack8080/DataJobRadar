'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FehlerAnzeige } from '@/components/ui/fehler-anzeige';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { Skeleton } from '@/components/ui/skeleton';
import { useApi } from '@/hooks/use-api';
import type { JobsSeite } from '@/lib/api';
import { formatDatum, formatGehalt } from '@/lib/utils';

export default function AnzeigenSeite() {
  const [suche, setSuche] = useState('');
  const [skill, setSkill] = useState('');
  const parameter = new URLSearchParams();
  if (suche) parameter.set('suche', suche);
  if (skill) parameter.set('skill', skill);
  parameter.set('limit', '25');

  const seite = useApi<JobsSeite>(`/jobs?${parameter.toString()}`);

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Stellenanzeigen</h1>
        <p className="text-sm text-muted-foreground">
          Aktuelle Treffer mit Filtern auf Volltext und Skill.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Filter</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row">
          <input
            value={suche}
            onChange={(ereignis) => setSuche(ereignis.target.value)}
            placeholder="Suche (Titel oder Unternehmen)"
            className="flex-1 rounded-md border bg-background px-3 py-2 text-sm shadow-card focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <input
            value={skill}
            onChange={(ereignis) => setSkill(ereignis.target.value)}
            placeholder="Skill (z.B. Python)"
            className="rounded-md border bg-background px-3 py-2 text-sm shadow-card focus:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:w-56"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ergebnisse</CardTitle>
        </CardHeader>
        <CardContent>
          {seite.isLoading && <Skeleton className="h-64 w-full" />}
          {seite.error && <FehlerAnzeige meldung="Stellenanzeigen konnten nicht geladen werden." />}
          {!seite.isLoading && !seite.error && (!seite.data || seite.data.treffer.length === 0) && (
            <LeererZustand titel="Keine Treffer fuer die aktuellen Filter." />
          )}
          {!seite.isLoading && !seite.error && seite.data && seite.data.treffer.length > 0 && (
            <ul className="divide-y">
              {seite.data.treffer.map((eintrag) => (
                <li key={eintrag.kennung} className="grid gap-2 py-4 sm:grid-cols-[1fr,auto] sm:items-start">
                  <div>
                    <p className="text-sm font-medium">{eintrag.titel}</p>
                    <p className="text-xs text-muted-foreground">
                      {[eintrag.unternehmen, eintrag.stadt, eintrag.bundesland].filter(Boolean).join(' - ')}
                    </p>
                    {eintrag.skills.length > 0 && (
                      <p className="mt-2 flex flex-wrap gap-1">
                        {eintrag.skills.slice(0, 8).map((wert) => (
                          <span
                            key={wert}
                            className="rounded-full border bg-muted/60 px-2 py-0.5 text-xs text-muted-foreground"
                          >
                            {wert}
                          </span>
                        ))}
                      </p>
                    )}
                  </div>
                  <div className="text-right text-xs text-muted-foreground sm:min-w-32">
                    <p className="kennzahl text-sm font-medium text-foreground">
                      {formatGehalt(eintrag.gehalt_mittel)}
                    </p>
                    <p>{formatDatum(eintrag.veroeffentlicht_am)}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
