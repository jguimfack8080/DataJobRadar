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

export function formatDatum(wert: string | Date | null | undefined): string {
  if (!wert) return '-';
  const datum = typeof wert === 'string' ? new Date(wert) : wert;
  if (Number.isNaN(datum.getTime())) return '-';
  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium' }).format(datum);
}
