'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect } from 'react';
import {
  BarChart3,
  Bookmark,
  BookOpen,
  Briefcase,
  Building2,
  LineChart,
  MapPin,
  Sparkles,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useNavigation } from './navigation-context';
import { useJobSpeicher } from '@/hooks/use-job-speicher';
import { ProfilWidget } from './profil-widget';

const navigation = [
  { name: 'Uebersicht', href: '/', icon: BarChart3 },
  { name: 'Stellenanzeigen', href: '/anzeigen', icon: Briefcase },
  { name: 'Skills', href: '/skills', icon: Sparkles },
  { name: 'Unternehmen', href: '/unternehmen', icon: Building2 },
  { name: 'Staedte', href: '/staedte', icon: MapPin },
  { name: 'Trends', href: '/trends', icon: LineChart },
  { name: 'Wiki', href: '/wiki', icon: BookOpen },
];

const QUELLEN = ['Bundesagentur f. Arbeit', 'Adzuna', 'Arbeitnow', 'Jooble', 'JSearch', 'The Muse', 'Remotive', 'Jobicy', 'RemoteOK'];

export function Sidebar() {
  const pfad = usePathname();
  const { mobileOffen, schliessen } = useNavigation();
  const { anzahlGespeichert } = useJobSpeicher();

  useEffect(() => {
    schliessen();
  }, [pfad, schliessen]);

  useEffect(() => {
    if (!mobileOffen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') schliessen();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [mobileOffen, schliessen]);

  useEffect(() => {
    if (mobileOffen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = '';
      };
    }
    return undefined;
  }, [mobileOffen]);

  return (
    <>
      <div
        onClick={schliessen}
        aria-hidden
        className={cn(
          'fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-200 ease-sanft lg:hidden',
          mobileOffen ? 'opacity-100' : 'pointer-events-none opacity-0'
        )}
      />
      <aside
        id="hauptnavigation"
        aria-label="Hauptnavigation"
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85%] flex-col border-r bg-card shadow-xl transition-transform duration-200 ease-sanft',
          'lg:sticky lg:top-0 lg:z-auto lg:h-screen lg:w-56 lg:max-w-none lg:shadow-none',
          mobileOffen ? 'translate-x-0' : '-translate-x-full',
          'lg:translate-x-0'
        )}
      >
        <div className="flex h-14 items-center justify-between px-5">
          <span className="text-sm font-semibold tracking-tight">Data Job Radar</span>
          <button
            type="button"
            onClick={schliessen}
            className="inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground lg:hidden"
            aria-label="Navigation schliessen"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-3">
          {navigation.map((eintrag) => {
            const aktiv = pfad === eintrag.href;
            const Symbol = eintrag.icon;
            return (
              <Link
                key={eintrag.href}
                href={eintrag.href}
                className={cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors duration-150 ease-sanft',
                  aktiv
                    ? 'bg-muted text-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                <Symbol className="h-4 w-4" aria-hidden />
                {eintrag.name}
              </Link>
            );
          })}
          <Link
            href="/gespeichert"
            className={cn(
              'flex items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-colors duration-150 ease-sanft',
              pfad === '/gespeichert'
                ? 'bg-muted text-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )}
          >
            <span className="flex items-center gap-3">
              <Bookmark className="h-4 w-4" aria-hidden />
              Gespeichert
            </span>
            {anzahlGespeichert > 0 && (
              <span className="rounded-full bg-cyan-500/15 px-2 py-0.5 text-[10px] font-semibold text-cyan-600 dark:text-cyan-400">
                {anzahlGespeichert}
              </span>
            )}
          </Link>
        </nav>

        <div className="border-t px-5 py-4">
          <ProfilWidget />
        </div>

        <div className="border-t px-5 py-4">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Datenquellen
          </p>
          <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
            {QUELLEN.map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </div>

        <div className="border-t px-5 py-3">
          <p className="text-[10px] text-muted-foreground/60">
            Projekt von <span className="font-medium text-muted-foreground">Jordan Jeuna</span>
          </p>
        </div>
      </aside>
    </>
  );
}
