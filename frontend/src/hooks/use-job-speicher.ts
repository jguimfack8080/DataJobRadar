'use client';

import { useCallback, useEffect, useState } from 'react';
import type { Job } from '@/lib/api';

const SCHLUESSEL = 'djr_speicher';

export type JobStatus = 'gesehen' | 'gespeichert' | 'beworben';

export interface JobSnapshot {
  kennung: string;
  titel: string;
  unternehmen: string | null;
  stadt: string | null;
  bundesland: string | null;
  quelle: string | null;
  angebots_url: string | null;
  veroeffentlicht_am: string | null;
  gehalt_mittel: number | null;
  gespeichert_am: string;
}

interface JobEintrag {
  status: JobStatus[];
  snapshot: JobSnapshot;
}

type Speicher = Record<string, JobEintrag>;

function lesen(): Speicher {
  if (typeof window === 'undefined') return {};
  try {
    return JSON.parse(localStorage.getItem(SCHLUESSEL) ?? '{}') as Speicher;
  } catch {
    return {};
  }
}

function schreiben(speicher: Speicher): void {
  try {
    localStorage.setItem(SCHLUESSEL, JSON.stringify(speicher));
  } catch {
    // localStorage voll oder nicht verfuegbar
  }
}

function jobSnapshot(job: Job): JobSnapshot {
  return {
    kennung: job.kennung,
    titel: job.titel,
    unternehmen: job.unternehmen,
    stadt: job.stadt,
    bundesland: job.bundesland,
    quelle: job.quelle,
    angebots_url: job.angebots_url,
    veroeffentlicht_am: job.veroeffentlicht_am,
    gehalt_mittel: job.gehalt_mittel,
    gespeichert_am: new Date().toISOString(),
  };
}

export function useJobSpeicher() {
  const [speicher, setSpeicher] = useState<Speicher>({});

  useEffect(() => {
    setSpeicher(lesen());
    const handler = (e: StorageEvent) => {
      if (e.key === SCHLUESSEL) setSpeicher(lesen());
    };
    window.addEventListener('storage', handler);
    return () => window.removeEventListener('storage', handler);
  }, []);

  const markiereGesehen = useCallback(
    (job: Job) => {
      setSpeicher((aktuell) => {
        const eintrag = aktuell[job.kennung];
        if (eintrag?.status.includes('gesehen')) return aktuell;
        const naechster: Speicher = {
          ...aktuell,
          [job.kennung]: {
            status: [...(eintrag?.status ?? []), 'gesehen'],
            snapshot: eintrag?.snapshot ?? jobSnapshot(job),
          },
        };
        schreiben(naechster);
        return naechster;
      });
    },
    []
  );

  const toggleGespeichert = useCallback(
    (job: Job) => {
      setSpeicher((aktuell) => {
        const eintrag = aktuell[job.kennung];
        const hatGespeichert = eintrag?.status.includes('gespeichert') ?? false;
        const neuerStatus: JobStatus[] = hatGespeichert
          ? (eintrag?.status ?? []).filter((s) => s !== 'gespeichert')
          : [...(eintrag?.status ?? []), 'gespeichert'];
        const naechster: Speicher = {
          ...aktuell,
          [job.kennung]: {
            status: neuerStatus,
            snapshot: eintrag?.snapshot ?? jobSnapshot(job),
          },
        };
        schreiben(naechster);
        return naechster;
      });
    },
    []
  );

  const setzeBeworben = useCallback(
    (job: Job) => {
      setSpeicher((aktuell) => {
        const eintrag = aktuell[job.kennung];
        const neuerStatus: JobStatus[] = Array.from(
          new Set([...(eintrag?.status ?? []), 'gespeichert', 'beworben'])
        );
        const naechster: Speicher = {
          ...aktuell,
          [job.kennung]: {
            status: neuerStatus,
            snapshot: eintrag?.snapshot ?? jobSnapshot(job),
          },
        };
        schreiben(naechster);
        return naechster;
      });
    },
    []
  );

  const toggleBeworben = useCallback(
    (job: Job) => {
      setSpeicher((aktuell) => {
        const eintrag = aktuell[job.kennung];
        const hatBeworben = eintrag?.status.includes('beworben') ?? false;
        const neuerStatus: JobStatus[] = hatBeworben
          ? (eintrag?.status ?? []).filter((s) => s !== 'beworben')
          : Array.from(new Set([...(eintrag?.status ?? []), 'gespeichert', 'beworben']));
        const naechster: Speicher = {
          ...aktuell,
          [job.kennung]: {
            status: neuerStatus,
            snapshot: eintrag?.snapshot ?? jobSnapshot(job),
          },
        };
        schreiben(naechster);
        return naechster;
      });
    },
    []
  );

  const entfernen = useCallback(
    (kennung: string) => {
      setSpeicher((aktuell) => {
        const { [kennung]: _entfernt, ...rest } = aktuell;
        schreiben(rest);
        return rest;
      });
    },
    []
  );

  const getStatus = useCallback(
    (kennung: string): JobStatus[] => speicher[kennung]?.status ?? [],
    [speicher]
  );

  const alleGespeicherten = useCallback(
    (): JobSnapshot[] =>
      Object.values(speicher)
        .filter((e) => e.status.includes('gespeichert'))
        .map((e) => e.snapshot)
        .sort((a, b) => b.gespeichert_am.localeCompare(a.gespeichert_am)),
    [speicher]
  );

  const alleBeworben = useCallback(
    (): JobSnapshot[] =>
      Object.values(speicher)
        .filter((e) => e.status.includes('beworben'))
        .map((e) => e.snapshot)
        .sort((a, b) => b.gespeichert_am.localeCompare(a.gespeichert_am)),
    [speicher]
  );

  const anzahlGespeichert = Object.values(speicher).filter((e) =>
    e.status.includes('gespeichert')
  ).length;

  const anzahlBeworben = Object.values(speicher).filter((e) =>
    e.status.includes('beworben')
  ).length;

  return {
    markiereGesehen,
    toggleGespeichert,
    toggleBeworben,
    setzeBeworben,
    entfernen,
    getStatus,
    alleGespeicherten,
    alleBeworben,
    anzahlGespeichert,
    anzahlBeworben,
  };
}
