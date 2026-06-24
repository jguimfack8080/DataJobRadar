'use client';

import { CheckCircle2, ExternalLink, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { QUELLEN_BESCHRIFTUNG } from '@/lib/api';
import { cn, formatDatumZeit, formatGehalt } from '@/lib/utils';
import { type JobSnapshot, useJobSpeicher } from '@/hooks/use-job-speicher';

export default function GespeichertSeite() {
  const { alleGespeicherten, alleBeworben, setzeBeworben, entfernen, anzahlGespeichert, anzahlBeworben } =
    useJobSpeicher();

  const gespeichert = alleGespeicherten();
  const beworben = alleBeworben();

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">Gespeicherte Stellen</h1>
        <p className="text-sm text-muted-foreground">
          Ihre lokal gespeicherten und beworbenen Anzeigen. Die Daten liegen ausschliesslich in
          Ihrem Browser und werden nicht synchronisiert.
        </p>
      </header>

      <div className="rounded-md border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-xs text-amber-700 dark:text-amber-400">
        Hinweis: Gespeicherte Anzeigen koennen jederzeit von der Original-Quelle entfernt werden.
        Bewerben Sie sich zeitnah, um keine Frist zu verpassen.
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <ZaehlerKarte label="Gespeichert" anzahl={anzahlGespeichert} farbe="cyan" />
        <ZaehlerKarte label="Beworben" anzahl={anzahlBeworben} farbe="emerald" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            Gespeichert
            {gespeichert.length > 0 && (
              <span className="ml-2 text-xs font-normal text-muted-foreground">
                {gespeichert.length} {gespeichert.length === 1 ? 'Anzeige' : 'Anzeigen'}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {gespeichert.length === 0 ? (
            <LeererZustand titel="Noch keine Anzeigen gespeichert." />
          ) : (
            <ul className="divide-y">
              {gespeichert.map((snap) => (
                <li key={snap.kennung} className="py-4">
                  <SnapKarte
                    snap={snap}
                    onBeworben={() =>
                      setzeBeworben({
                        kennung: snap.kennung,
                        titel: snap.titel,
                        unternehmen: snap.unternehmen,
                        stadt: snap.stadt,
                        bundesland: snap.bundesland,
                        quelle: snap.quelle,
                        angebots_url: snap.angebots_url,
                        veroeffentlicht_am: snap.veroeffentlicht_am,
                        gehalt_min: null,
                        gehalt_max: null,
                        gehalt_mittel: snap.gehalt_mittel,
                        waehrung: null,
                        vertragstyp: null,
                        vertragszeit: null,
                        kategorie: null,
                        skills: [],
                        quell_id: null,
                      })
                    }
                    onEntfernen={() => entfernen(snap.kennung)}
                    zeigeBewerbungsButton
                  />
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Beworben
            {beworben.length > 0 && (
              <span className="ml-2 text-xs font-normal text-muted-foreground">
                {beworben.length} {beworben.length === 1 ? 'Bewerbung' : 'Bewerbungen'}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {beworben.length === 0 ? (
            <LeererZustand titel="Noch keine Bewerbungen markiert." />
          ) : (
            <ul className="divide-y">
              {beworben.map((snap) => (
                <li key={snap.kennung} className="py-4">
                  <SnapKarte
                    snap={snap}
                    onEntfernen={() => entfernen(snap.kennung)}
                    zeigeBewerbungsButton={false}
                  />
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ZaehlerKarte({
  label,
  anzahl,
  farbe,
}: {
  label: string;
  anzahl: number;
  farbe: 'cyan' | 'emerald';
}) {
  const farbenKlassen = {
    cyan: 'border-cyan-500/30 bg-cyan-500/5 text-cyan-600 dark:text-cyan-400',
    emerald: 'border-emerald-500/30 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400',
  };
  return (
    <div className={cn('rounded-md border px-4 py-3', farbenKlassen[farbe])}>
      <p className="text-2xl font-semibold">{anzahl}</p>
      <p className="text-xs">{label}</p>
    </div>
  );
}

interface SnapKarteProps {
  snap: JobSnapshot;
  onBeworben?: () => void;
  onEntfernen: () => void;
  zeigeBewerbungsButton: boolean;
}

function SnapKarte({ snap, onBeworben, onEntfernen, zeigeBewerbungsButton }: SnapKarteProps) {
  const quellenLabel = snap.quelle ? (QUELLEN_BESCHRIFTUNG[snap.quelle] ?? snap.quelle) : null;
  const ortszeile = [snap.unternehmen, snap.stadt, snap.bundesland].filter(Boolean).join(' · ');

  return (
    <div className="grid gap-2 rounded-md p-2 -m-2 transition-colors hover:bg-muted/60">
      <div className="grid gap-2 sm:grid-cols-[1fr,auto] sm:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            {snap.angebots_url ? (
              <a
                href={snap.angebots_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm font-medium underline-offset-2 hover:underline"
              >
                {snap.titel}
                <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden />
              </a>
            ) : (
              <span className="text-sm font-medium">{snap.titel}</span>
            )}
            {quellenLabel && (
              <span className="rounded-full border bg-card px-2 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
                {quellenLabel}
              </span>
            )}
          </div>
          {ortszeile && (
            <p className="mt-0.5 text-xs text-muted-foreground">{ortszeile}</p>
          )}
          <p className="mt-1 text-xs text-muted-foreground">
            Gespeichert am {formatDatumZeit(snap.gespeichert_am)}
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 sm:min-w-36">
          <div className="text-right">
            <p className="kennzahl text-sm font-medium text-foreground">
              {formatGehalt(snap.gehalt_mittel)}
            </p>
            <p className="text-xs text-muted-foreground">
              {formatDatumZeit(snap.veroeffentlicht_am)}
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            {zeigeBewerbungsButton && onBeworben && (
              <button
                type="button"
                onClick={onBeworben}
                className="inline-flex items-center gap-1 rounded-md border bg-card px-2 py-1 text-[10px] font-medium text-muted-foreground transition-colors hover:border-emerald-500/50 hover:text-emerald-600 dark:hover:text-emerald-400"
              >
                <CheckCircle2 className="h-3 w-3" aria-hidden />
                Beworben
              </button>
            )}
            <button
              type="button"
              onClick={onEntfernen}
              title="Entfernen"
              className="inline-flex h-7 w-7 items-center justify-center rounded-md border bg-card text-muted-foreground transition-colors hover:border-red-500/40 hover:text-red-500"
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
