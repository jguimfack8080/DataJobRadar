import type { Metadata } from 'next';

export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL as string;
export const OG_IMAGE = `${SITE_URL}/og-image.png`;

export function seitenMetadata(
  slug: string,
  titel: string,
  beschreibung: string,
): Metadata {
  const url = `${SITE_URL}${slug}`;
  const vollTitel = `${titel} | Data Job Radar Deutschland`;
  return {
    title: titel,
    description: beschreibung,
    openGraph: {
      url,
      title: vollTitel,
      description: beschreibung,
      images: [{ url: OG_IMAGE, width: 1200, height: 630, alt: vollTitel }],
    },
    twitter: {
      title: vollTitel,
      description: beschreibung,
      images: [OG_IMAGE],
    },
  };
}
