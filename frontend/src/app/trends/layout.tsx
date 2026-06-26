import type { Metadata } from 'next';
import { seitenMetadata } from '@/lib/site-metadata';

export const metadata: Metadata = seitenMetadata(
  '/trends/',
  'Markttrends',
  'Zeitreihen und Gehaltsverteilungen nach Jobkategorie auf dem deutschen IT-Arbeitsmarkt: Data Engineering, Data Science, Analytics und mehr.',
);

export default function TrendsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
