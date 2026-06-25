'use client';

import { useEffect, useRef, useState } from 'react';
import { AlertCircle, CheckCircle2, Clock, RefreshCw, WifiOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { QuelleStatusEintrag, QuellenStatusAntwort } from '@/lib/api';

const POLL_MS = 60_000;

function formatZeitstempel(iso: string | null): string {
  if (!iso) return 'Noch kein Lauf';
  try {
    return new Intl.DateTimeFormat('de-DE', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Berlin',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function StatusPunkt({ aktiv, abgebrochen }: { aktiv: boolean; abgebrochen: boolean }) {
  if (abgebrochen) {
    return <span className="relative flex h-2 w-2">
      <span className="h-2 w-2 rounded-full bg-destructive" />
    </span>;
  }
  if (!aktiv) {
    return <span className="h-2 w-2 rounded-full bg-muted-foreground/40" />;
  }
  return (
    <span className="relative flex h-2 w-2">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
      <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
    </span>
  );
}

function QuotaLeiste({ prozent, monatlich }: { prozent: number; monatlich: boolean }) {
  const farbe =
    prozent >= 90 ? 'bg-destructive' :
    prozent >= 70 ? 'bg-amber-500' :
    'bg-emerald-500';

  return (
    <div className="mt-1.5 space-y-0.5">
      <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn('h-full rounded-full transition-all duration-500', farbe)}
          style={{ width: `${Math.min(prozent, 100)}%` }}
        />
      </div>
      <p className="text-[9px] text-muted-foreground">
        {Math.round(prozent)}% {monatlich ? 'diesen Monat' : 'gesamt'} verbraucht
      </p>
    </div>
  );
}

function QuelleKarte({ eintrag, hatDaten }: { eintrag: QuelleStatusEintrag; hatDaten: boolean }) {
  const aktiv = hatDaten && !eintrag.abgebrochen && eintrag.geladen > 0;

  return (
    <div
      className={cn(
        'flex flex-col gap-1.5 rounded-lg border p-3 transition-colors',
        eintrag.abgebrochen
          ? 'border-destructive/30 bg-destructive/5'
          : aktiv
          ? 'border-emerald-500/20 bg-emerald-500/5'
          : 'border-border bg-muted/20',
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <StatusPunkt aktiv={aktiv} abgebrochen={eintrag.abgebrochen} />
          <span className="truncate text-xs font-medium text-foreground">
            {eintrag.bezeichnung}
          </span>
        </div>
        {hatDaten && (
          <span className={cn(
            'shrink-0 text-[10px] font-semibold tabular-nums',
            aktiv ? 'text-emerald-600 dark:text-emerald-400' : 'text-muted-foreground',
          )}>
            {eintrag.gueltig.toLocaleString('de-DE')}
          </span>
        )}
      </div>

      {eintrag.abgebrochen && eintrag.abbruchgrund && (
        <p className="truncate text-[9px] text-destructive">{eintrag.abbruchgrund}</p>
      )}

      {eintrag.quota && (
        <QuotaLeiste prozent={eintrag.quota.prozent} monatlich={eintrag.quota.monatlich} />
      )}
    </div>
  );
}

export function QuellenStatus() {
  const [daten, setDaten] = useState<QuellenStatusAntwort | null>(null);
  const [ladend, setLadend] = useState(true);
  const [fehler, setFehler] = useState(false);
  const [letzteAktualisierung, setLetzteAktualisierung] = useState<Date | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const laden = async () => {
    try {
      const res = await fetch('/api/v1/quellen/status');
      if (!res.ok) throw new Error();
      const json = await res.json() as QuellenStatusAntwort;
      setDaten(json);
      setFehler(false);
      setLetzteAktualisierung(new Date());
    } catch {
      setFehler(true);
    } finally {
      setLadend(false);
    }
  };

  useEffect(() => {
    laden();
    timer.current = setInterval(laden, POLL_MS);
    return () => { if (timer.current) clearInterval(timer.current); };
  }, []);

  const hatDaten = !!daten?.zeitstempel;
  const abgebrochen = daten?.quellen.filter(q => q.abgebrochen).length ?? 0;
  const aktiv = daten?.quellen.filter(q => !q.abgebrochen && q.geladen > 0).length ?? 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <h2 className="text-sm font-semibold tracking-tight">Datenquellen</h2>
          <p className="text-[10px] text-muted-foreground">
            {hatDaten
              ? `Letzter Lauf: ${formatZeitstempel(daten!.zeitstempel)}`
              : 'Noch kein Pipeline-Lauf'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {hatDaten && (
            <div className="flex items-center gap-1.5 rounded-md border px-2 py-1">
              <CheckCircle2 className="h-3 w-3 text-emerald-500" />
              <span className="text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                {aktiv} aktiv
              </span>
              {abgebrochen > 0 && (
                <>
                  <span className="text-muted-foreground/40">|</span>
                  <AlertCircle className="h-3 w-3 text-destructive" />
                  <span className="text-[10px] font-medium text-destructive">
                    {abgebrochen} Fehler
                  </span>
                </>
              )}
            </div>
          )}
          <button
            type="button"
            onClick={laden}
            title="Aktualisieren"
            className="inline-flex h-7 w-7 items-center justify-center rounded-md border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <RefreshCw className={cn('h-3 w-3', ladend && 'animate-spin')} />
          </button>
        </div>
      </div>

      {fehler ? (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2">
          <WifiOff className="h-3.5 w-3.5 shrink-0 text-destructive" />
          <p className="text-xs text-destructive">Status nicht abrufbar</p>
        </div>
      ) : ladend && !daten ? (
        <div className="grid grid-cols-3 gap-2">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-2">
            {(daten?.quellen ?? []).map(eintrag => (
              <QuelleKarte key={eintrag.name} eintrag={eintrag} hatDaten={hatDaten} />
            ))}
          </div>
          {hatDaten && (
            <div className="flex items-center gap-1.5 text-[9px] text-muted-foreground/60">
              <Clock className="h-2.5 w-2.5" />
              Zahl = gueltige Stellen letzter Lauf. Aktualisierung alle 60 s.
            </div>
          )}
        </>
      )}
    </div>
  );
}
