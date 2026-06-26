import type { Metadata } from 'next';
import { seitenMetadata } from '@/lib/site-metadata';

export const metadata: Metadata = seitenMetadata(
  '/staedte/',
  'Staedte & Regionen',
  'Regionale Verteilung der IT-Jobs in Deutschland: Berlin, Muenchen, Hamburg, Frankfurt und mehr – mit Karte und Rangliste nach Stellenanzahl.',
);

export default function StaedteLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
