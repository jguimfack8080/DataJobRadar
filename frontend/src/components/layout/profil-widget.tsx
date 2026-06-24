'use client';

import type { FormEvent } from 'react';
import { useState } from 'react';
import { CircleCheck, CircleDashed, CircleX, LogIn, LogOut, User } from 'lucide-react';
import { type SyncStatus, useNutzerProfil } from '@/hooks/use-nutzer-profil';
import { cn } from '@/lib/utils';

function SyncPunkt({ status }: { status: SyncStatus }) {
  if (status === 'syncing') {
    return <CircleDashed className="h-3 w-3 animate-spin text-muted-foreground" aria-hidden />;
  }
  if (status === 'ok') {
    return <CircleCheck className="h-3 w-3 text-emerald-500" aria-hidden />;
  }
  if (status === 'fehler') {
    return <CircleX className="h-3 w-3 text-destructive" aria-hidden />;
  }
  return null;
}

const SYNC_TEXT: Record<SyncStatus, string> = {
  bereit: '',
  syncing: 'Synchronisiert...',
  ok: 'Synchronisiert',
  fehler: 'Sync-Fehler',
};

export function ProfilWidget() {
  const { username, syncStatus, anmelden, abmelden } = useNutzerProfil();
  const [entwurf, setEntwurf] = useState('');
  const [fehler, setFehler] = useState('');
  const [ladend, setLadend] = useState(false);

  const absenden = async (e: FormEvent) => {
    e.preventDefault();
    const name = entwurf.trim().toLowerCase();
    if (!/^[a-z0-9_]{3,30}$/.test(name)) {
      setFehler('3-30 Zeichen: a-z, 0-9, _');
      return;
    }
    setFehler('');
    setLadend(true);
    const ok = await anmelden(name);
    setLadend(false);
    if (!ok) setFehler('Server nicht erreichbar');
    else setEntwurf('');
  };

  if (username) {
    return (
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 flex-col gap-0.5">
          <div className="flex items-center gap-1.5">
            <User className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden />
            <span className="truncate text-xs font-medium">@{username}</span>
          </div>
          {syncStatus !== 'bereit' && (
            <div className="flex items-center gap-1 pl-4">
              <SyncPunkt status={syncStatus} />
              <span className={cn(
                'text-[10px]',
                syncStatus === 'fehler' ? 'text-destructive' : 'text-muted-foreground'
              )}>
                {SYNC_TEXT[syncStatus]}
              </span>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={abmelden}
          title="Abmelden"
          className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <LogOut className="h-3.5 w-3.5" aria-hidden />
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={absenden} className="space-y-2">
      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
        Profil
      </p>
      <div className="flex gap-1.5">
        <input
          type="text"
          value={entwurf}
          onChange={(e) => { setEntwurf(e.target.value); setFehler(''); }}
          placeholder="Username"
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
          spellCheck={false}
          maxLength={30}
          className="min-w-0 flex-1 rounded-md border bg-background px-2.5 py-1.5 text-xs shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <button
          type="submit"
          disabled={ladend || !entwurf.trim()}
          title="Verlauf abrufen"
          className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
        >
          <LogIn className="h-3.5 w-3.5" aria-hidden />
        </button>
      </div>
      {fehler && (
        <p className="text-[10px] text-destructive">{fehler}</p>
      )}
      <p className="text-[10px] leading-relaxed text-muted-foreground">
        Username sichert Ihren Verlauf geraeteuebergreifend. Kein Passwort erforderlich.
      </p>
    </form>
  );
}
