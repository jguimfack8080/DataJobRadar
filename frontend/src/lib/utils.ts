import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatZahl(wert: number | null | undefined, optionen?: Intl.NumberFormatOptions): string {
  if (wert === null || wert === undefined || Number.isNaN(wert)) return '-';
  return new Intl.NumberFormat('de-DE', optionen).format(wert);
}

export function formatGehalt(wert: number | null | undefined): string {
  if (wert === null || wert === undefined) return '-';
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(wert);
}

function zumDatum(wert: string | Date | null | undefined): Date | null {
  if (!wert) return null;
  const d = typeof wert === 'string' ? new Date(wert) : wert;
  return Number.isNaN(d.getTime()) ? null : d;
}

const BERLIN = 'Europe/Berlin';

export function formatDatum(wert: string | Date | null | undefined): string {
  const d = zumDatum(wert);
  if (!d) return '-';
  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium', timeZone: BERLIN }).format(d);
}

export function formatDatumZeit(wert: string | Date | null | undefined): string {
  const d = zumDatum(wert);
  if (!d) return '-';
  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium', timeStyle: 'short', timeZone: BERLIN }).format(d);
}
