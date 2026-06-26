import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ThemeProvider } from '@/components/layout/theme-provider';
import { NavigationProvider } from '@/components/layout/navigation-context';
import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';
import { SITE_URL, OG_IMAGE } from '@/lib/site-metadata';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter', display: 'swap' });

const TITEL = 'Data Job Radar Deutschland – IT-Arbeitsmarkt Analyse';
const BESCHREIBUNG =
  'Echtzeit-Analyse des IT-Arbeitsmarkts: 9 Quellen, taeglich aktualisiert. Skills, Staedte, Gehalt auf einen Blick.';

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: TITEL,
    template: '%s | Data Job Radar Deutschland',
  },
  description: BESCHREIBUNG,
  openGraph: {
    type: 'website',
    siteName: 'Data Job Radar Deutschland',
    url: SITE_URL,
    title: TITEL,
    description: BESCHREIBUNG,
    images: [{ url: OG_IMAGE, width: 1200, height: 630, alt: TITEL }],
  },
  twitter: {
    card: 'summary_large_image',
    title: TITEL,
    description: BESCHREIBUNG,
    images: [OG_IMAGE],
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className={inter.variable} suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ThemeProvider>
          <NavigationProvider>
            <div className="flex min-h-screen">
              <Sidebar />
              <div className="flex flex-1 flex-col">
                <Topbar />
                <main className="flex-1 px-4 py-6 sm:px-6 lg:px-10">{children}</main>
              </div>
            </div>
          </NavigationProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
