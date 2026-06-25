'use client';

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Bookmark, BookmarkCheck, CheckCircle2, ExternalLink, Filter, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FehlerAnzeige } from '@/components/ui/fehler-anzeige';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { Skeleton } from '@/components/ui/skeleton';
import type { FilterFacetten, Job, JobsFilter, JobsSeite } from '@/lib/api';
import { ApiFehler, QUELLEN_BESCHRIFTUNG, endpunkte, holen } from '@/lib/api';
import { cn, formatDatumZeit, formatGehalt } from '@/lib/utils';
import { type JobStatus, useJobSpeicher } from '@/hooks/use-job-speicher';

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
  const [nurNeue, setNurNeue] = useState(false);

  const speicher = useJobSpeicher();

  useEffect(() => {
    endpunkte.facetten().then(setFacetten).catch(() => setFacetten(null));
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
        setJobs((bestehend) =>
          cursor ? [...bestehend, ...ergebnis.treffer] : ergebnis.treffer
        );
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

  const sichtbareJobs = useMemo(() => {
    if (!nurNeue) return jobs;
    return jobs.filter((j) => !speicher.getStatus(j.kennung).includes('gesehen'));
  }, [jobs, nurNeue, speicher]);

  const anwenden = (e: React.FormEvent) => {
    e.preventDefault();
    setAngewendet(entwurf);
  };

  const zuruecksetzen = () => {
    setEntwurf(LEER);
    setAngewendet(LEER);
  };

  const setText =
    (feld: keyof FilterZustand) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const wert = e.target.value;
      setEntwurf((alt) => ({ ...alt, [feld]: wert || undefined }) as FilterZustand);
    };

  const setZahl =
    (feld: keyof FilterZustand) => (e: React.ChangeEvent<HTMLInputElement>) => {
      const wert = e.target.value;
      setEntwurf((alt) => ({ ...alt, [feld]: wert ? Number(wert) : undefined }) as FilterZustand);
    };

  const skillsUmschalten = (skill: string) => {
    setEntwurf((alt) => {
      const aktuell = alt.skill ?? [];
      return {
        ...alt,
        skill: aktuell.includes(skill)
          ? aktuell.filter((s) => s !== skill)
          : [...aktuell, skill],
      };
    });
  };

  const quellenUmschalten = (quelle: string) => {
    setEntwurf((alt) => {
      const aktuell = alt.quelle ?? [];
      return {
        ...alt,
        quelle: aktuell.includes(quelle)
          ? aktuell.filter((q) => q !== quelle)
          : [...aktuell, quelle],
      };
    });
  };

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">Stellenanzeigen</h1>
        <p className="text-sm text-muted-foreground">
          Vollstaendige Filtersuite ueber alle Quellen. Anzeige speichern oder als beworben
          markieren, um den Ueberblick zu behalten.
        </p>
      </header>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-4 w-4" aria-hidden />
            <span>Filter</span>
            {aktivAnzahl > 0 && (
              <span className="rounded-full bg-accent px-2 py-0.5 text-xs font-medium text-accent-foreground">
                {aktivAnzahl}
              </span>
            )}
          </CardTitle>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setFilterOffen((v) => !v)}
              className="rounded-md border bg-card px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
            >
              {filterOffen ? 'Einklappen' : 'Mehr Filter'}
            </button>
            {aktivAnzahl > 0 && (
              <button
                type="button"
                onClick={zuruecksetzen}
                className="inline-flex items-center gap-1 rounded-md border bg-card px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
              >
                <X className="h-3 w-3" aria-hidden />
                Zuruecksetzen
              </button>
            )}
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

            {facetten && facetten.quellen.length > 0 && (
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
            )}

            {filterOffen && (
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
                        onChange={(e) =>
                          setEntwurf((alt) => ({ ...alt, nur_mit_gehalt: e.target.checked }))
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

                {facetten && facetten.skills.length > 0 && (
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
                )}
              </>
            )}

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
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <CardTitle>
            Ergebnisse
            {jobs.length > 0 && (
              <span className="ml-2 text-xs font-normal text-muted-foreground">
                {sichtbareJobs.length}
                {nurNeue && sichtbareJobs.length !== jobs.length
                  ? ` von ${jobs.length}`
                  : ''}
                {nextKeyset ? ' (weitere verfuegbar)' : ' angezeigt'}
              </span>
            )}
          </CardTitle>
          <button
            type="button"
            onClick={() => setNurNeue((v) => !v)}
            className={cn(
              'rounded-md border px-3 py-1.5 text-xs transition-colors',
              nurNeue
                ? 'border-foreground bg-foreground text-background'
                : 'bg-card text-muted-foreground hover:text-foreground'
            )}
          >
            Nur Neue
          </button>
        </CardHeader>
        <CardContent>
          {ladend === 'init' && <Skeleton className="h-64 w-full" />}
          {fehler && <FehlerAnzeige meldung={fehler} />}
          {ladend !== 'init' && !fehler && sichtbareJobs.length === 0 && (
            <LeererZustand
              titel={
                nurNeue
                  ? 'Alle geladenen Anzeigen wurden bereits angesehen.'
                  : 'Keine Treffer fuer die aktuellen Filter.'
              }
            />
          )}
          {sichtbareJobs.length > 0 && (
            <>
              <ul className="divide-y">
                {sichtbareJobs.map((job) => (
                  <li key={job.kennung} className="py-4">
                    <JobKarte
                      job={job}
                      status={speicher.getStatus(job.kennung)}
                      onGesehen={() => speicher.markiereGesehen(job)}
                      onToggleGespeichert={() => speicher.toggleGespeichert(job)}
                      onBeworben={() => speicher.toggleBeworben(job)}
                    />
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

interface JobKarteProps {
  job: Job;
  status: JobStatus[];
  onGesehen: () => void;
  onToggleGespeichert: () => void;
  onBeworben: () => void;
}

function JobKarte({ job, status, onGesehen, onToggleGespeichert, onBeworben }: JobKarteProps) {
  const istGesehen = status.includes('gesehen');
  const istGespeichert = status.includes('gespeichert');
  const istBeworben = status.includes('beworben');
  const quellenLabel = job.quelle ? (QUELLEN_BESCHRIFTUNG[job.quelle] ?? job.quelle) : null;
  const ortszeile = [job.unternehmen, job.stadt, job.bundesland].filter(Boolean).join(' · ');

  const [delta, setDelta] = useState(0);
  const [animiert, setAnimiert] = useState(false);

  const startX = useRef(0);
  const startY = useRef(0);
  const richtung = useRef<'h' | 'v' | null>(null);
  const aktiv = useRef(false);
  const hatGewischt = useRef(false);
  const cbRef = useRef({ onBeworben, onToggleGespeichert });

  useEffect(() => {
    cbRef.current = { onBeworben, onToggleGespeichert };
  });

  const SCHWELLE = 80;

  const abschliessen = useCallback((dx: number) => {
    aktiv.current = false;
    hatGewischt.current = Math.abs(dx) > 8;
    const warH = richtung.current === 'h';
    richtung.current = null;
    setAnimiert(true);

    if (warH && dx > SCHWELLE) {
      setDelta(100);
      setTimeout(() => { cbRef.current.onBeworben(); setDelta(0); }, 180);
    } else if (warH && dx < -SCHWELLE) {
      setDelta(-100);
      setTimeout(() => { cbRef.current.onToggleGespeichert(); setDelta(0); }, 180);
    } else {
      setDelta(0);
    }
    setTimeout(() => setAnimiert(false), 600);
  }, []);

  const onPointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    startX.current = e.clientX;
    startY.current = e.clientY;
    richtung.current = null;
    aktiv.current = true;
    hatGewischt.current = false;
    setAnimiert(false);
  }, []);

  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      if (!aktiv.current) return;
      const dx = e.clientX - startX.current;
      const dy = e.clientY - startY.current;
      if (richtung.current === null) {
        if (Math.abs(dx) < 5 && Math.abs(dy) < 5) return;
        richtung.current = Math.abs(dx) > Math.abs(dy) ? 'h' : 'v';
      }
      if (richtung.current !== 'h') return;
      setDelta(dx);
    };
    const onUp = (e: PointerEvent) => {
      if (!aktiv.current) return;
      abschliessen(e.clientX - startX.current);
    };
    window.addEventListener('pointermove', onMove, { passive: true });
    window.addEventListener('pointerup', onUp);
    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
  }, [abschliessen]);

  const fortschrittRechts = Math.min(1, Math.max(0, delta / SCHWELLE));
  const fortschrittLinks = Math.min(1, Math.max(0, -delta / SCHWELLE));
  const passiertSchwelleRechts = delta > SCHWELLE;
  const passiertSchwelleLinks = delta < -SCHWELLE;

  return (
    <div className="relative overflow-hidden rounded-md select-none">
      {/* Swipe-rechts Hintergrund: Beworben toggle */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 flex items-center rounded-md bg-emerald-500/10 pl-5"
        style={{ opacity: fortschrittRechts }}
      >
        <div
          className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400"
          style={{
            transform: `scale(${0.6 + fortschrittRechts * 0.55})`,
            transition: 'transform 0.1s ease-out',
            filter: passiertSchwelleRechts ? 'brightness(1.15)' : 'none',
          }}
        >
          {istBeworben
            ? <><CheckCircle2 className="h-6 w-6" aria-hidden /><span className="text-sm font-semibold">Entfernen</span></>
            : <><CheckCircle2 className="h-6 w-6" aria-hidden /><span className="text-sm font-semibold">Beworben</span></>
          }
        </div>
      </div>

      {/* Swipe-links Hintergrund: Gespeichert */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 flex items-center justify-end rounded-md bg-cyan-500/10 pr-5"
        style={{ opacity: fortschrittLinks }}
      >
        <div
          className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400"
          style={{
            transform: `scale(${0.6 + fortschrittLinks * 0.55})`,
            transition: 'transform 0.1s ease-out',
            filter: passiertSchwelleLinks ? 'brightness(1.15)' : 'none',
          }}
        >
          <span className="text-sm font-semibold">
            {istGespeichert ? 'Entfernen' : 'Speichern'}
          </span>
          {istGespeichert
            ? <BookmarkCheck className="h-6 w-6" aria-hidden />
            : <Bookmark className="h-6 w-6" aria-hidden />
          }
        </div>
      </div>

      {/* Karte (verschiebt sich) */}
      <div
        onPointerDown={onPointerDown}
        className="relative touch-pan-y rounded-md p-2 -m-2 hover:bg-muted/60"
        style={{
          transform: `translateX(${delta}px) rotate(${delta * 0.008}deg)`,
          ...(animiert ? {
            transitionProperty: 'transform',
            transitionDuration: '0.38s',
            transitionTimingFunction: 'cubic-bezier(0.34,1.56,0.64,1)',
          } : {
            transitionProperty: 'background-color',
            transitionDuration: '150ms',
            transitionTimingFunction: 'ease',
          }),
          willChange: 'transform',
        }}
      >
        <div className="grid gap-2 sm:grid-cols-[1fr,auto] sm:items-start">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              {job.angebots_url ? (
                <a
                  href={job.angebots_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => {
                    if (hatGewischt.current) { e.preventDefault(); return; }
                    onGesehen();
                  }}
                  className="inline-flex items-center gap-1.5 text-sm font-medium underline-offset-2 hover:underline"
                  aria-label={`Anzeige '${job.titel}' oeffnen`}
                >
                  {job.titel}
                  <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden />
                </a>
              ) : (
                <span className="text-sm font-medium">{job.titel}</span>
              )}
              {quellenLabel && (
                <span className="rounded-full border bg-card px-2 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
                  {quellenLabel}
                </span>
              )}
              {istBeworben && (
                <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                  Beworben
                </span>
              )}
              {istGespeichert && !istBeworben && (
                <span className="rounded-full bg-cyan-500/10 px-2 py-0.5 text-[10px] font-medium text-cyan-600 dark:text-cyan-400">
                  Gespeichert
                </span>
              )}
              {istGesehen && !istGespeichert && !istBeworben && (
                <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
                  Gesehen
                </span>
              )}
            </div>

            {ortszeile && (
              <p className="mt-0.5 text-xs text-muted-foreground">{ortszeile}</p>
            )}

            <p className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
              {job.kategorie && <span>Kategorie: {job.kategorie}</span>}
              {job.vertragszeit && <span>Zeit: {job.vertragszeit}</span>}
              {job.vertragstyp && <span>Typ: {job.vertragstyp}</span>}
            </p>

            {job.skills.length > 0 && (
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
            )}
          </div>

          <div className="flex flex-col items-end gap-2 sm:min-w-36">
            <div className="text-right">
              <p className="kennzahl text-sm font-medium text-foreground">
                {formatGehalt(job.gehalt_mittel)}
              </p>
              <p className="text-xs text-muted-foreground">{formatDatumZeit(job.veroeffentlicht_am)}</p>
            </div>

            <div className="flex items-center gap-1.5">
              {istGespeichert && !istBeworben && (
                <button
                  type="button"
                  onClick={onBeworben}
                  title="Als beworben markieren"
                  className="inline-flex items-center gap-1 rounded-md border bg-card px-2 py-1 text-[10px] font-medium text-muted-foreground transition-colors hover:border-emerald-500/50 hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  <CheckCircle2 className="h-3 w-3" aria-hidden />
                  Beworben
                </button>
              )}
              <button
                type="button"
                onClick={onToggleGespeichert}
                title={istGespeichert ? 'Aus Gespeicherten entfernen' : 'Speichern'}
                className={cn(
                  'inline-flex h-7 w-7 items-center justify-center rounded-md border transition-colors',
                  istGespeichert
                    ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 hover:bg-cyan-500/20'
                    : 'bg-card text-muted-foreground hover:border-cyan-500/40 hover:text-cyan-600 dark:hover:text-cyan-400'
                )}
              >
                {istGespeichert ? (
                  <BookmarkCheck className="h-3.5 w-3.5" aria-hidden />
                ) : (
                  <Bookmark className="h-3.5 w-3.5" aria-hidden />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
