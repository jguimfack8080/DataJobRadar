import type { Metadata } from 'next';
import { seitenMetadata } from '@/lib/site-metadata';

export const metadata: Metadata = {
  ...seitenMetadata(
    '/gespeichert/',
    'Gespeicherte Jobs',
    'Deine gespeicherten und beworbenen IT-Stellen – verwalte deinen Bewerbungsprozess direkt im Browser.',
  ),
  robots: { index: false, follow: false },
};

export default function GespeichertLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
