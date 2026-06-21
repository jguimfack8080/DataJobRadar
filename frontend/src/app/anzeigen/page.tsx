'use client';

import { useCallback, useEffect, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FehlerAnzeige } from '@/components/ui/fehler-anzeige';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { Skeleton } from '@/components/ui/skeleton';
import type { Job, JobsSeite } from '@/lib/api';
import { ApiFehler, holen } from '@/lib/api';
import { formatDatum, formatGehalt } from '@/lib/utils';

const SEITENGROESSE = 25;

export default function AnzeigenSeite() {
  const [sucheEingabe, setSucheEingabe] = useState('');
  const [skillEingabe, setSkillEingabe] = useState('');
  const [suche, setSuche] = useState('');
  const [skill, setSkill] = useState('');
  const [jobs, setJobs] = useState<Job[]>([]);
  const [nextKeyset, setNextKeyset] = useState<string | null>(null);
  const [ladend, setLadend] = useState<'init' | 'mehr' | null>('init');
  const [fehler, setFehler] = useState<string | null>(null);

  const seiteHolen = useCallback(
    async (cursor: string | null) => {
      try {
        const ergebnis = await holen<JobsSeite>('/jobs', {
          suche: suche || undefined,
          skill: skill || undefined,
          limit: SEITENGROESSE,
          nach: cursor ?? undefined,
        });
        setJobs((bestehend) => (cursor ? [...bestehend, ...ergebnis.treffer] : ergebnis.treffer));
        setNextKeyset(ergebnis.naechstes_keyset);
        setFehler(null);
      } catch (problem) {
        if (problem instanceof ApiFehler) {
          setFehler(problem.meldung);
        } else if (problem instanceof Error) {
          setFehler(problem.message);
        } else {
          setFehler('Unbekannter Fehler');
        }
      } finally {
        setLadend(null);
      }
    },
    [suche, skill]
  );

  useEffect(() => {
    setLadend('init');
    setJobs([]);
    setNextKeyset(null);
    void seiteHolen(null);
  }, [seiteHolen]);

  const filterAnwenden = (ereignis: React.FormEvent) => {
    ereignis.preventDefault();
    setSuche(sucheEingabe.trim());
    setSkill(skillEingabe.trim());
  };

  const mehrLaden = () => {
    if (!nextKeyset) return;
    setLadend('mehr');
    void seiteHolen(nextKeyset);
  };

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Stellenanzeigen</h1>
        <p className="text-sm text-muted-foreground">
          Aktuelle Treffer mit Filtern auf Volltext und Skill. Klicken Sie eine Karte an, um die
          Original-Anzeige bei Adzuna zu oeffnen.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Filter</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={filterAnwenden} className="flex flex-col gap-3 sm:flex-row">
            <input
              value={sucheEingabe}
              onChange={(ereignis) => setSucheEingabe(ereignis.target.value)}
              placeholder="Suche (Titel oder Unternehmen)"
              className="flex-1 rounded-md border bg-background px-3 py-2 text-sm shadow-card focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <input
              value={skillEingabe}
              onChange={(ereignis) => setSkillEingabe(ereignis.target.value)}
              placeholder="Skill (z.B. Python)"
              className="rounded-md border bg-background px-3 py-2 text-sm shadow-card focus:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:w-56"
            />
            <button
              type="submit"
              className="inline-flex items-center justify-center rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background transition-colors hover:opacity-90"
            >
              Anwenden
            </button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Ergebnisse
            {jobs.length > 0 ? (
              <span className="ml-2 text-xs text-muted-foreground">
                {jobs.length} angezeigt
              </span>
            ) : null}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {ladend === 'init' && <Skeleton className="h-64 w-full" />}
          {fehler && <FehlerAnzeige meldung={fehler} />}
          {ladend !== 'init' && !fehler && jobs.length === 0 && (
            <LeererZustand titel="Keine Treffer fuer die aktuellen Filter." />
          )}
          {jobs.length > 0 && (
            <>
              <ul className="divide-y">
                {jobs.map((eintrag) => (
                  <li key={eintrag.kennung} className="py-4">
                    <JobKarte job={eintrag} />
                  </li>
                ))}
              </ul>
              <div className="mt-6 flex flex-col items-center gap-2">
                {nextKeyset ? (
                  <button
                    type="button"
                    onClick={mehrLaden}
                    disabled={ladend === 'mehr'}
                    className="inline-flex items-center justify-center rounded-md border bg-card px-5 py-2 text-sm font-medium text-foreground shadow-card transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {ladend === 'mehr' ? 'Wird geladen...' : 'Mehr laden'}
                  </button>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    Ende der Ergebnisse erreicht.
                  </p>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function JobKarte({ job }: { job: Job }) {
  const ortszeile = [job.unternehmen, job.stadt, job.bundesland].filter(Boolean).join(' - ');
  const Inhalt = (
    <div className="grid gap-2 sm:grid-cols-[1fr,auto] sm:items-start">
      <div>
        <p className="flex items-center gap-2 text-sm font-medium">
          <span>{job.titel}</span>
          {job.angebots_url ? <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" aria-hidden /> : null}
        </p>
        {ortszeile ? <p className="text-xs text-muted-foreground">{ortszeile}</p> : null}
        {job.skills.length > 0 ? (
          <p className="mt-2 flex flex-wrap gap-1">
            {job.skills.slice(0, 8).map((wert) => (
              <span
                key={wert}
                className="rounded-full border bg-muted/60 px-2 py-0.5 text-xs text-muted-foreground"
              >
                {wert}
              </span>
            ))}
          </p>
        ) : null}
      </div>
      <div className="text-right text-xs text-muted-foreground sm:min-w-32">
        <p className="kennzahl text-sm font-medium text-foreground">
          {formatGehalt(job.gehalt_mittel)}
        </p>
        <p>{formatDatum(job.veroeffentlicht_am)}</p>
      </div>
    </div>
  );

  if (job.angebots_url) {
    return (
      <a
        href={job.angebots_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block rounded-md p-2 -m-2 transition-colors hover:bg-muted/60 focus:bg-muted/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-label={`Anzeige '${job.titel}' bei Adzuna oeffnen`}
      >
        {Inhalt}
      </a>
    );
  }
  return <div className="p-2 -m-2">{Inhalt}</div>;
}
