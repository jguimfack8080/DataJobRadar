import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ThemeProvider } from '@/components/layout/theme-provider';
import { NavigationProvider } from '@/components/layout/navigation-context';
import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter', display: 'swap' });

export const metadata: Metadata = {
  title: 'Data Job Radar Deutschland',
  description:
    'Analyseplattform fuer den deutschen IT-Arbeitsmarkt aus fuenf Quellen: Bundesagentur fuer Arbeit, Adzuna, The Muse, Remotive und Jobicy.',
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
