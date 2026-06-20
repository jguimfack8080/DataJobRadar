'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BarChart3, Briefcase, Building2, LineChart, MapPin, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Uebersicht', href: '/', icon: BarChart3 },
  { name: 'Stellenanzeigen', href: '/anzeigen', icon: Briefcase },
  { name: 'Skills', href: '/skills', icon: Sparkles },
  { name: 'Unternehmen', href: '/unternehmen', icon: Building2 },
  { name: 'Staedte', href: '/staedte', icon: MapPin },
  { name: 'Trends', href: '/trends', icon: LineChart },
];

export function Sidebar() {
  const pfad = usePathname();
  return (
    <aside className="hidden w-56 shrink-0 border-r bg-card lg:flex lg:flex-col">
      <div className="flex h-14 items-center px-5">
        <span className="text-sm font-semibold tracking-tight">Data Job Radar</span>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-3">
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
      </nav>
      <div className="px-5 py-4 text-xs text-muted-foreground">
        Quelle: Adzuna API (Land: de)
      </div>
    </aside>
  );
}
