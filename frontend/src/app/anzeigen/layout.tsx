import type { Metadata } from 'next';
import { seitenMetadata } from '@/lib/site-metadata';

export const metadata: Metadata = seitenMetadata(
  '/anzeigen/',
  'Stellenanzeigen',
  'Alle aktuellen Data- und IT-Stellenanzeigen in Deutschland – gefiltert nach Skills, Standort, Gehalt und Unternehmen. Taeglich aus 9 Quellen aktualisiert.',
);

export default function AnzeigenLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
