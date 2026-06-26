import type { Metadata } from 'next';
import { seitenMetadata } from '@/lib/site-metadata';

export const metadata: Metadata = seitenMetadata(
  '/unternehmen/',
  'Unternehmen',
  'Welche Unternehmen in Deutschland die meisten Data- und IT-Stellen ausschreiben – Rangliste nach Stellenanzahl und mittlerem Gehalt.',
);

export default function UnternehmenLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
