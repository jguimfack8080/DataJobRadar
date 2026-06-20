'use client';

import useSWR from 'swr';

const fetcher = async (url: string) => {
  const antwort = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!antwort.ok) {
    const nutzlast = await antwort.json().catch(() => ({}));
    throw new Error(nutzlast.meldung ?? `HTTP ${antwort.status}`);
  }
  return antwort.json();
};

export function useApi<T>(pfad: string | null) {
  const basis = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api/v1';
  const url = pfad ? `${basis}${pfad}` : null;
  return useSWR<T>(url, fetcher, {
    revalidateOnFocus: false,
    revalidateIfStale: false,
    keepPreviousData: true,
  });
}
