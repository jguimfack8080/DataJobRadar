import type { Metadata } from 'next';
import { seitenMetadata } from '@/lib/site-metadata';

export const metadata: Metadata = seitenMetadata(
  '/skills/',
  'Skills & Technologien',
  'Die gefragtesten IT-Skills und Technologien auf dem deutschen Arbeitsmarkt: Python, SQL, Spark, AWS, dbt und mehr – live aus Tausenden Stellenanzeigen.',
);

export default function SkillsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
