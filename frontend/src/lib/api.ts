const basis = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api/v1';

export class ApiFehler extends Error {
  constructor(public code: string, public meldung: string, public status: number) {
    super(meldung);
    this.name = 'ApiFehler';
  }
}

type Wert = string | number | boolean | undefined | null;

export async function holen<T>(pfad: string, parameter?: Record<string, Wert | Wert[]>): Promise<T> {
  const url = new URL(
    `${basis}${pfad}`,
    typeof window === 'undefined' ? 'http://localhost' : window.location.origin
  );
  if (parameter) {
    for (const [name, wert] of Object.entries(parameter)) {
      if (wert === undefined || wert === null || wert === '') continue;
      if (Array.isArray(wert)) {
        for (const teil of wert) {
          if (teil === undefined || teil === null || teil === '') continue;
          url.searchParams.append(name, String(teil));
        }
      } else {
        url.searchParams.set(name, String(wert));
      }
    }
  }
  const antwort = await fetch(url.toString().replace('http://localhost', ''), {
    headers: { Accept: 'application/json' },
    cache: 'no-store',
  });
  if (!antwort.ok) {
    let nutzlast: { code?: string; meldung?: string } = {};
    try {
      nutzlast = await antwort.json();
    } catch {
      // ignoriere parse-Fehler
    }
    throw new ApiFehler(
      nutzlast.code ?? 'unbekannt',
      nutzlast.meldung ?? `HTTP ${antwort.status}`,
      antwort.status
    );
  }
  return antwort.json() as Promise<T>;
}

export const endpunkte = {
  kennzahlen: () => holen<KennzahlenGesamt>('/stats'),
  jobs: (filter: JobsFilter) =>
    holen<JobsSeite>('/jobs', filter as unknown as Record<string, Wert | Wert[]>),
  facetten: () => holen<FilterFacetten>('/jobs/facetten'),
  quellenVerteilung: () => holen<QuellenVerteilung[]>('/jobs/quellen'),
  topSkills: (limit = 12) => holen<SkillKennzahl[]>('/skills', { limit }),
  topUnternehmen: (limit = 10) => holen<UnternehmensKennzahl[]>('/companies', { limit }),
  topStaedte: (limit = 10) => holen<StadtKennzahl[]>('/cities', { limit }),
  zeitreihe: (tage = 30) => holen<ZeitreihePunkt[]>('/trends/zeitreihe', { tage }),
  gehaltsverteilung: (gruppierung: 'kategorie' | 'stadt' | 'bundesland' | 'quelle' = 'kategorie') =>
    holen<GehaltsverteilungEintrag[]>('/trends/gehaltsverteilung', { gruppierung }),
};

export const QUELLEN_BESCHRIFTUNG: Record<string, string> = {
  bundesagentur: 'Bundesagentur f. Arbeit',
  adzuna: 'Adzuna',
  arbeitnow: 'Arbeitnow',
  jooble: 'Jooble',
  jsearch: 'JSearch',
  muse: 'The Muse',
  remotive: 'Remotive',
  jobicy: 'Jobicy',
  remoteok: 'RemoteOK',
};

export interface QuotaInfo {
  verbraucht: number;
  grenze: number;
  prozent: number;
  monatlich: boolean;
  reset_datum: string | null;
}

export interface QuelleStatusEintrag {
  name: string;
  bezeichnung: string;
  geladen: number;
  gueltig: number;
  quarantaene: number;
  abgebrochen: boolean;
  abbruchgrund: string | null;
  quota: QuotaInfo | null;
}

export interface QuellenStatusAntwort {
  zeitstempel: string | null;
  quellen: QuelleStatusEintrag[];
}

export interface KennzahlenGesamt {
  anzahl_jobs: number;
  anzahl_unternehmen: number;
  anzahl_standorte: number;
  anzahl_quellen: number;
  gehalt_mittel: number | null;
  frueheste_anzeige: string | null;
  spaeteste_anzeige: string | null;
}

export interface Job {
  kennung: string;
  quelle: string | null;
  quell_id: string | null;
  titel: string;
  unternehmen: string | null;
  stadt: string | null;
  bundesland: string | null;
  gehalt_min: number | null;
  gehalt_max: number | null;
  gehalt_mittel: number | null;
  waehrung: string | null;
  vertragstyp: string | null;
  vertragszeit: string | null;
  veroeffentlicht_am: string | null;
  kategorie: string | null;
  skills: string[];
  angebots_url: string | null;
}

export interface JobsSeite {
  treffer: Job[];
  naechstes_keyset: string | null;
}

export interface JobsFilter {
  suche?: string;
  stadt?: string;
  bundesland?: string;
  unternehmen?: string;
  kategorie?: string;
  vertragstyp?: string;
  vertragszeit?: string;
  waehrung?: string;
  gehalt_min?: number;
  gehalt_max?: number;
  nur_mit_gehalt?: boolean;
  veroeffentlicht_seit?: string;
  veroeffentlicht_bis?: string;
  skill?: string[];
  quelle?: string[];
  nach?: string;
  limit?: number;
}

export interface FilterFacetten {
  kategorien: string[];
  vertragstypen: string[];
  vertragszeiten: string[];
  bundeslaender: string[];
  staedte: string[];
  skills: string[];
  quellen: string[];
}

export interface SkillKennzahl {
  skill: string;
  anzahl: number;
  anzahl_jobs: number;
}

export interface UnternehmensKennzahl {
  unternehmen: string;
  anzahl_jobs: number;
  gehalt_mittel: number | null;
}

export interface StadtKennzahl {
  stadt: string;
  bundesland: string | null;
  anzahl_jobs: number;
  gehalt_mittel: number | null;
}

export interface ZeitreihePunkt {
  tag: string;
  anzahl: number;
}

export interface GehaltsverteilungEintrag {
  gruppe: string;
  anzahl: number;
  gehalt_p25: number | null;
  gehalt_median: number | null;
  gehalt_p75: number | null;
  gehalt_mittel: number | null;
}

export interface QuellenVerteilung {
  quelle: string;
  anzahl_jobs: number;
  gehalt_mittel: number | null;
}
