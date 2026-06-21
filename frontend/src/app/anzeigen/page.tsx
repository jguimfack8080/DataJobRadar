'use client';

import { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ExternalLink, Filter, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FehlerAnzeige } from '@/components/ui/fehler-anzeige';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { Skeleton } from '@/components/ui/skeleton';
import type { FilterFacetten, Job, JobsFilter, JobsSeite } from '@/lib/api';
import { ApiFehler, QUELLEN_BESCHRIFTUNG, endpunkte, holen } from '@/lib/api';
import { formatDatum, formatGehalt } from '@/lib/utils';

const SEITENGROESSE = 25;

type FilterZustand = Omit<JobsFilter, 'nach' | 'limit'>;

const LEER: FilterZustand = {};

function filterAusUrl(params: URLSearchParams): FilterZustand {
  const aus: FilterZustand = {};
  const setStr = (feld: keyof FilterZustand, name: string) => {
    const w = params.get(name);
    if (w) (aus as Record<string, unknown>)[feld] = w;
  };
  setStr('suche', 'suche');
  setStr('stadt', 'stadt');
  setStr('bundesland', 'bundesland');
  setStr('unternehmen', 'unternehmen');
  setStr('kategorie', 'kategorie');
  setStr('vertragstyp', 'vertragstyp');
  setStr('vertragszeit', 'vertragszeit');
  setStr('waehrung', 'waehrung');
  setStr('veroeffentlicht_seit', 'veroeffentlicht_seit');
  setStr('veroeffentlicht_bis', 'veroeffentlicht_bis');
  const gmin = params.get('gehalt_min');
  if (gmin) aus.gehalt_min = Number(gmin);
  const gmax = params.get('gehalt_max');
  if (gmax) aus.gehalt_max = Number(gmax);
  const mitGehalt = params.get('nur_mit_gehalt');
  if (mitGehalt === 'true' || mitGehalt === '1') aus.nur_mit_gehalt = true;
  const skills = params.getAll('skill');
  if (skills.length > 0) aus.skill = skills;
  const quellen = params.getAll('quelle');
  if (quellen.length > 0) aus.quelle = quellen;
  return aus;
}

export default function AnzeigenSeite() {
  return (
    <Suspense fallback={<Skeleton className="h-64 w-full" />}>
      <AnzeigenInhalt />
    </Suspense>
  );
}

function AnzeigenInhalt() {
  const urlParams = useSearchParams();
  const initial = useMemo(
    () => filterAusUrl(urlParams ?? new URLSearchParams()),
    [urlParams]
  );
  const [entwurf, setEntwurf] = useState<FilterZustand>(initial);
  const [angewendet, setAngewendet] = useState<FilterZustand>(initial);
  const [facetten, setFacetten] = useState<FilterFacetten | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [nextKeyset, setNextKeyset] = useState<string | null>(null);
  const [ladend, setLadend] = useState<'init' | 'mehr' | null>('init');
  const [fehler, setFehler] = useState<string | null>(null);
  const [filterOffen, setFilterOffen] = useState(false);

  useEffect(() => {
    endpunkte
      .facetten()
      .then(setFacetten)
      .catch(() => setFacetten(null));
  }, []);

  useEffect(() => {
    setEntwurf(initial);
    setAngewendet(initial);
  }, [initial]);

  const seiteHolen = useCallback(
    async (cursor: string | null) => {
      try {
        const ergebnis = await holen<JobsSeite>('/jobs', {
          ...angewendet,
          limit: SEITENGROESSE,
          nach: cursor ?? undefined,
        });
        setJobs((bestehend) => (cursor ? [...bestehend, ...ergebnis.treffer] : ergebnis.treffer));
        setNextKeyset(ergebnis.naechstes_keyset);
        setFehler(null);
      } catch (problem) {
        if (problem instanceof ApiFehler) setFehler(problem.meldung);
        else if (problem instanceof Error) setFehler(problem.message);
        else setFehler('Unbekannter Fehler');
      } finally {
        setLadend(null);
      }
    },
    [angewendet]
  );

  useEffect(() => {
    setLadend('init');
    setJobs([]);
    setNextKeyset(null);
    void seiteHolen(null);
  }, [seiteHolen]);

  const aktivAnzahl = useMemo(() => {
    let n = 0;
    for (const [, wert] of Object.entries(angewendet)) {
      if (wert === undefined || wert === null || wert === '' || wert === false) continue;
      if (Array.isArray(wert)) n += wert.length;
      else n += 1;
    }
    return n;
  }, [angewendet]);

  const anwenden = (ereignis: React.FormEvent) => {
    ereignis.preventDefault();
    setAngewendet(entwurf);
  };

  const zuruecksetzen = () => {
    setEntwurf(LEER);
    setAngewendet(LEER);
  };

  const setText =
    (feld: keyof FilterZustand) =>
    (ereignis: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const wert = ereignis.target.value;
      setEntwurf((alt) => ({ ...alt, [feld]: wert ? wert : undefined }) as FilterZustand);
    };

  const setZahl =
    (feld: keyof FilterZustand) => (ereignis: React.ChangeEvent<HTMLInputElement>) => {
      const wert = ereignis.target.value;
      setEntwurf((alt) => ({ ...alt, [feld]: wert ? Number(wert) : undefined }) as FilterZustand);
    };

  const skillsUmschalten = (skill: string) => {
    setEntwurf((alt) => {
      const aktuell = alt.skill ?? [];
      const enthalten = aktuell.includes(skill);
      return {
        ...alt,
        skill: enthalten ? aktuell.filter((s) => s !== skill) : [...aktuell, skill],
      };
    });
  };

  const quellenUmschalten = (quelle: string) => {
    setEntwurf((alt) => {
      const aktuell = alt.quelle ?? [];
      const enthalten = aktuell.includes(quelle);
      return {
        ...alt,
        quelle: enthalten ? aktuell.filter((q) => q !== quelle) : [...aktuell, quelle],
      };
    });
  };

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">Stellenanzeigen</h1>
        <p className="text-sm text-muted-foreground">
          Vollstaendige Filtersuite ueber alle Quellen. Klicken Sie eine Karte an, um zur
          Original-Anzeige zu springen.
        </p>
      </header>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-4 w-4" aria-hidden />
            <span>Filter</span>
            {aktivAnzahl > 0 ? (
              <span className="rounded-full bg-accent px-2 py-0.5 text-xs font-medium text-accent-foreground">
                {aktivAnzahl}
              </span>
            ) : null}
          </CardTitle>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setFilterOffen((v) => !v)}
              className="rounded-md border bg-card px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
            >
              {filterOffen ? 'Einklappen' : 'Mehr Filter'}
            </button>
            {aktivAnzahl > 0 ? (
              <button
                type="button"
                onClick={zuruecksetzen}
                className="inline-flex items-center gap-1 rounded-md border bg-card px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
              >
                <X className="h-3 w-3" aria-hidden />
                Zuruecksetzen
              </button>
            ) : null}
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={anwenden} className="flex flex-col gap-4">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <Feld label="Volltext (Titel oder Unternehmen)">
                <input
                  type="text"
                  value={entwurf.suche ?? ''}
                  onChange={setText('suche')}
                  placeholder="z.B. Spark"
                  className={eingabeStil}
                />
              </Feld>
              <Feld label="Unternehmen">
                <input
                  type="text"
                  value={entwurf.unternehmen ?? ''}
                  onChange={setText('unternehmen')}
                  placeholder="z.B. ZEISS"
                  className={eingabeStil}
                />
              </Feld>
              <Feld label="Stadt">
                <input
                  type="text"
                  list="staedte-facetten"
                  value={entwurf.stadt ?? ''}
                  onChange={setText('stadt')}
                  placeholder="z.B. Berlin"
                  className={eingabeStil}
                />
                <datalist id="staedte-facetten">
                  {facetten?.staedte.map((s) => <option key={s} value={s} />)}
                </datalist>
              </Feld>
            </div>

            {facetten && facetten.quellen.length > 0 ? (
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Datenquellen (Mehrfachauswahl, ODER-Verknuepfung)
                </p>
                <div className="flex flex-wrap gap-2">
                  {facetten.quellen.map((quelle) => {
                    const aktiv = (entwurf.quelle ?? []).includes(quelle);
                    return (
                      <button
                        type="button"
                        key={quelle}
                        onClick={() => quellenUmschalten(quelle)}
                        className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                          aktiv
                            ? 'bg-foreground text-background'
                            : 'bg-card text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        {QUELLEN_BESCHRIFTUNG[quelle] ?? quelle}
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : null}

            {filterOffen ? (
              <>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <Feld label="Bundesland">
                    <select
                      value={entwurf.bundesland ?? ''}
                      onChange={setText('bundesland')}
                      className={eingabeStil}
                    >
                      <option value="">- alle -</option>
                      {facetten?.bundeslaender.map((b) => (
                        <option key={b} value={b}>{b}</option>
                      ))}
                    </select>
                  </Feld>
                  <Feld label="Kategorie">
                    <select
                      value={entwurf.kategorie ?? ''}
                      onChange={setText('kategorie')}
                      className={eingabeStil}
                    >
                      <option value="">- alle -</option>
                      {facetten?.kategorien.map((k) => (
                        <option key={k} value={k}>{k}</option>
                      ))}
                    </select>
                  </Feld>
                  <Feld label="Waehrung (ISO 4217)">
                    <input
                      type="text"
                      maxLength={3}
                      value={entwurf.waehrung ?? ''}
                      onChange={setText('waehrung')}
                      placeholder="EUR"
                      className={eingabeStil + ' uppercase'}
                    />
                  </Feld>
                  <Feld label="Vertragstyp">
                    <select
                      value={entwurf.vertragstyp ?? ''}
                      onChange={setText('vertragstyp')}
                      className={eingabeStil}
                    >
                      <option value="">- beliebig -</option>
                      {facetten?.vertragstypen.map((v) => (
                        <option key={v} value={v}>{v}</option>
                      ))}
                    </select>
                  </Feld>
                  <Feld label="Vertragszeit">
                    <select
                      value={entwurf.vertragszeit ?? ''}
                      onChange={setText('vertragszeit')}
                      className={eingabeStil}
                    >
                      <option value="">- beliebig -</option>
                      {facetten?.vertragszeiten.map((v) => (
                        <option key={v} value={v}>{v}</option>
                      ))}
                    </select>
                  </Feld>
                  <Feld label="Nur mit Gehaltsangabe">
                    <label className="flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm shadow-card">
                      <input
                        type="checkbox"
                        checked={entwurf.nur_mit_gehalt ?? false}
                        onChange={(ereignis) =>
                          setEntwurf((alt) => ({ ...alt, nur_mit_gehalt: ereignis.target.checked }))
                        }
                      />
                      <span>Anzeigen ohne Gehalt ausblenden</span>
                    </label>
                  </Feld>
                </div>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <Feld label="Gehalt min (EUR)">
                    <input
                      type="number"
                      min={0}
                      step={1000}
                      value={entwurf.gehalt_min ?? ''}
                      onChange={setZahl('gehalt_min')}
                      placeholder="0"
                      className={eingabeStil}
                    />
                  </Feld>
                  <Feld label="Gehalt max (EUR)">
                    <input
                      type="number"
                      min={0}
                      step={1000}
                      value={entwurf.gehalt_max ?? ''}
                      onChange={setZahl('gehalt_max')}
                      placeholder="999000"
                      className={eingabeStil}
                    />
                  </Feld>
                  <Feld label="Veroeffentlicht ab">
                    <input
                      type="date"
                      value={entwurf.veroeffentlicht_seit ?? ''}
                      onChange={setText('veroeffentlicht_seit')}
                      className={eingabeStil}
                    />
                  </Feld>
                  <Feld label="Veroeffentlicht bis">
                    <input
                      type="date"
                      value={entwurf.veroeffentlicht_bis ?? ''}
                      onChange={setText('veroeffentlicht_bis')}
                      className={eingabeStil}
                    />
                  </Feld>
                </div>

                {facetten && facetten.skills.length > 0 ? (
                  <div>
                    <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Skills (Mehrfachauswahl, UND-Verknuepfung)
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {facetten.skills.map((skill) => {
                        const aktiv = (entwurf.skill ?? []).includes(skill);
                        return (
                          <button
                            type="button"
                            key={skill}
                            onClick={() => skillsUmschalten(skill)}
                            className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                              aktiv
                                ? 'bg-foreground text-background'
                                : 'bg-card text-muted-foreground hover:text-foreground'
                            }`}
                          >
                            {skill}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ) : null}
              </>
            ) : null}

            <div className="flex justify-end">
              <button
                type="submit"
                className="inline-flex items-center justify-center rounded-md bg-foreground px-5 py-2 text-sm font-medium text-background transition-colors hover:opacity-90"
              >
                Filter anwenden
              </button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Ergebnisse
            {jobs.length > 0 ? (
              <span className="ml-2 text-xs text-muted-foreground">
                {jobs.length} {nextKeyset ? '(weitere verfuegbar)' : 'angezeigt'}
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
                    onClick={() => {
                      setLadend('mehr');
                      void seiteHolen(nextKeyset);
                    }}
                    disabled={ladend === 'mehr'}
                    className="inline-flex items-center justify-center rounded-md border bg-card px-5 py-2 text-sm font-medium text-foreground shadow-card transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {ladend === 'mehr' ? 'Wird geladen...' : 'Mehr laden'}
                  </button>
                ) : (
                  <p className="text-xs text-muted-foreground">Ende der Ergebnisse erreicht.</p>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

const eingabeStil =
  'w-full rounded-md border bg-background px-3 py-2 text-sm shadow-card focus:outline-none focus-visible:ring-2 focus-visible:ring-ring';

function Feld({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      {children}
    </label>
  );
}

function JobKarte({ job }: { job: Job }) {
  const ortszeile = [job.unternehmen, job.stadt, job.bundesland].filter(Boolean).join(' - ');
  const quellenLabel = job.quelle
    ? QUELLEN_BESCHRIFTUNG[job.quelle] ?? job.quelle
    : null;
  const Inhalt = (
    <div className="grid gap-2 sm:grid-cols-[1fr,auto] sm:items-start">
      <div>
        <p className="flex flex-wrap items-center gap-2 text-sm font-medium">
          <span>{job.titel}</span>
          {job.angebots_url ? (
            <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" aria-hidden />
          ) : null}
          {quellenLabel ? (
            <span className="rounded-full border bg-card px-2 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
              {quellenLabel}
            </span>
          ) : null}
        </p>
        {ortszeile ? <p className="text-xs text-muted-foreground">{ortszeile}</p> : null}
        <p className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
          {job.kategorie ? <span>Kategorie: {job.kategorie}</span> : null}
          {job.vertragszeit ? <span>Zeit: {job.vertragszeit}</span> : null}
          {job.vertragstyp ? <span>Typ: {job.vertragstyp}</span> : null}
        </p>
        {job.skills.length > 0 ? (
          <p className="mt-2 flex flex-wrap gap-1">
            {job.skills.slice(0, 10).map((wert) => (
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
        aria-label={`Anzeige '${job.titel}' bei ${quellenLabel ?? 'der Quelle'} oeffnen`}
      >
        {Inhalt}
      </a>
    );
  }
  return <div className="p-2 -m-2">{Inhalt}</div>;
}
