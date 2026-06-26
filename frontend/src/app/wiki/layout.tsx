import type { Metadata } from 'next';
import { seitenMetadata } from '@/lib/site-metadata';

export const metadata: Metadata = seitenMetadata(
  '/wiki/',
  'Wiki & Dokumentation',
  'Technische Dokumentation des Data Job Radar: Architektur, Datenfluss, Datenmodell, eingesetzte Technologien und Deployment-Topologie.',
);

export default function WikiLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
