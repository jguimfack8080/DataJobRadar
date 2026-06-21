'use client';

import { Menu, Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { useNavigation } from './navigation-context';

export function Topbar() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const { oeffnen } = useNavigation();
  const [montiert, setMontiert] = useState(false);
  useEffect(() => setMontiert(true), []);
  const dunkel = resolvedTheme === 'dark';

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-background/90 px-4 backdrop-blur lg:px-10">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={oeffnen}
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground lg:hidden"
          aria-label="Navigation oeffnen"
          aria-controls="hauptnavigation"
        >
          <Menu className="h-4 w-4" />
        </button>
        <span className="text-sm font-semibold tracking-tight lg:hidden">Data Job Radar</span>
        <div className="hidden items-center gap-3 text-sm text-muted-foreground lg:flex">
          <span>Marktanalyse Deutschland</span>
          <span className="rounded-full border px-2 py-0.5 text-xs">Live</span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {montiert && (
          <button
            type="button"
            onClick={() => setTheme(dunkel ? 'light' : 'dark')}
            className="inline-flex h-9 w-9 items-center justify-center rounded-md border bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label={dunkel ? 'Helles Thema aktivieren' : 'Dunkles Thema aktivieren'}
          >
            {dunkel ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        )}
      </div>
    </header>
  );
}
