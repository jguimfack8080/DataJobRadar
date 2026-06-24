'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

const PROFIL_SCHLUESSEL = 'djr_profil';
const SPEICHER_SCHLUESSEL = 'djr_speicher';
const USERNAME_MUSTER = /^[a-z0-9_]{3,30}$/;
const POLL_MS = 30_000;

export type SyncStatus = 'bereit' | 'syncing' | 'ok' | 'fehler';

const STATUS_RANG: Record<string, number> = { beworben: 3, gespeichert: 2, gesehen: 1 };

function profilLesen(): string {
  if (typeof window === 'undefined') return '';
  try {
    const roh = localStorage.getItem(PROFIL_SCHLUESSEL);
    return roh ? (JSON.parse(roh).username ?? '') : '';
  } catch {
    return '';
  }
}

function speicherLesen(): Record<string, any> {
  if (typeof window === 'undefined') return {};
  try {
    return JSON.parse(localStorage.getItem(SPEICHER_SCHLUESSEL) ?? '{}');
  } catch {
    return {};
  }
}

function zuEintraege(speicher: Record<string, any>) {
  return Object.entries(speicher).map(([kennung, e]) => ({
    kennung,
    status: e?.status ?? [],
    snapshot: e?.snapshot ?? null,
  }));
}

export function useNutzerProfil() {
  const [username, setUsername] = useState('');
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('bereit');
  const letzterHash = useRef('');

  useEffect(() => {
    setUsername(profilLesen());
  }, []);

  const syncZuServer = useCallback(async (name: string): Promise<void> => {
    const aktuell = localStorage.getItem(SPEICHER_SCHLUESSEL) ?? '{}';
    if (aktuell === letzterHash.current) return;
    letzterHash.current = aktuell;
    setSyncStatus('syncing');
    try {
      const res = await fetch(`/api/v1/nutzer/${name}/aktivitaet`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ eintraege: zuEintraege(speicherLesen()) }),
      });
      if (!res.ok) throw new Error();
      setSyncStatus('ok');
    } catch {
      setSyncStatus('fehler');
    }
  }, []);

  const ladenvomServer = useCallback(async (name: string): Promise<boolean> => {
    setSyncStatus('syncing');
    try {
      const res = await fetch(`/api/v1/nutzer/${name}/aktivitaet`);
      if (!res.ok) throw new Error();
      const { eintraege } = await res.json() as { eintraege: Array<{ kennung: string; status: string[]; snapshot: any }> };

      const lokal: Record<string, any> = speicherLesen();
      for (const e of eintraege) {
        const vorh = lokal[e.kennung];
        if (!vorh) {
          lokal[e.kennung] = { status: e.status, snapshot: e.snapshot };
        } else {
          const vereint = Array.from(new Set([...vorh.status, ...e.status])).sort(
            (a, b) => (STATUS_RANG[b] ?? 0) - (STATUS_RANG[a] ?? 0)
          );
          lokal[e.kennung] = { status: vereint, snapshot: vorh.snapshot ?? e.snapshot };
        }
      }
      const fusioniert = JSON.stringify(lokal);
      localStorage.setItem(SPEICHER_SCHLUESSEL, fusioniert);
      window.dispatchEvent(new StorageEvent('storage', { key: SPEICHER_SCHLUESSEL }));
      setSyncStatus('ok');
      return true;
    } catch {
      setSyncStatus('fehler');
      return false;
    }
  }, []);

  const anmelden = useCallback(async (name: string): Promise<boolean> => {
    if (!USERNAME_MUSTER.test(name)) return false;
    const ok = await ladenvomServer(name);
    if (ok) {
      localStorage.setItem(PROFIL_SCHLUESSEL, JSON.stringify({ username: name }));
      setUsername(name);
      await syncZuServer(name);
    }
    return ok;
  }, [ladenvomServer, syncZuServer]);

  const abmelden = useCallback(() => {
    localStorage.removeItem(PROFIL_SCHLUESSEL);
    setUsername('');
    setSyncStatus('bereit');
    letzterHash.current = '';
  }, []);

  useEffect(() => {
    if (!username) return;
    const id = setInterval(() => void syncZuServer(username), POLL_MS);
    return () => clearInterval(id);
  }, [username, syncZuServer]);

  useEffect(() => {
    if (!username) return;
    const flush = () => void syncZuServer(username);
    window.addEventListener('beforeunload', flush);
    return () => window.removeEventListener('beforeunload', flush);
  }, [username, syncZuServer]);

  return { username, syncStatus, anmelden, abmelden };
}
