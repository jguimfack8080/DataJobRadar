'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardKennzahl, CardTitle } from '@/components/ui/card';
import { FehlerAnzeige } from '@/components/ui/fehler-anzeige';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { Skeleton } from '@/components/ui/skeleton';
import { BalkenDiagramm } from '@/components/charts/balken-diagramm';
import { LinienDiagramm } from '@/components/charts/linien-diagramm';
import { useApi } from '@/hooks/use-api';
import { formatGehalt, formatZahl } from '@/lib/utils';
import type {
  KennzahlenGesamt,
  SkillKennzahl,
  StadtKennzahl,
  UnternehmensKennzahl,
  ZeitreihePunkt,
} from '@/lib/api';

const anzeigenLink = (filter: Record<string, string>) => {
  const params = new URLSearchParams(filter).toString();
  return `/anzeigen/?${params}`;
};

export default function UebersichtSeite() {
  const kennzahlen = useApi<KennzahlenGesamt>('/stats');
  const skills = useApi<SkillKennzahl[]>('/skills?limit=12');
  const staedte = useApi<StadtKennzahl[]>('/cities?limit=10');
  const unternehmen = useApi<UnternehmensKennzahl[]>('/companies?limit=10');
  const zeitreihe = useApi<ZeitreihePunkt[]>('/trends/zeitreihe?tage=30');

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-8">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">Uebersicht</h1>
        <p className="text-sm text-muted-foreground">
          Klicken Sie eine Kachel, einen Balken oder einen Listeneintrag an, um direkt zu den
          passenden Stellenanzeigen zu springen.
        </p>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KennzahlenKachel
          titel="Aktive Anzeigen"
          ziel="/anzeigen/"
          ladend={kennzahlen.isLoading}
          fehler={kennzahlen.error}
          wert={formatZahl(kennzahlen.data?.anzahl_jobs ?? 0)}
        />
        <KennzahlenKachel
          titel="Unternehmen"
          ziel="/unternehmen/"
          ladend={kennzahlen.isLoading}
          fehler={kennzahlen.error}
          wert={formatZahl(kennzahlen.data?.anzahl_unternehmen ?? 0)}
        />
        <KennzahlenKachel
          titel="Standorte"
          ziel="/staedte/"
          ladend={kennzahlen.isLoading}
          fehler={kennzahlen.error}
          wert={formatZahl(kennzahlen.data?.anzahl_standorte ?? 0)}
        />
        <KennzahlenKachel
          titel="Mittleres Gehalt"
          ziel={anzeigenLink({ nur_mit_gehalt: 'true' })}
          ladend={kennzahlen.isLoading}
          fehler={kennzahlen.error}
          wert={formatGehalt(kennzahlen.data?.gehalt_mittel ?? null)}
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Neue Anzeigen je Tag</CardTitle>
            <p className="text-xs text-muted-foreground">Zeitreihe der letzten 30 Tage.</p>
          </CardHeader>
          <CardContent>
            <DiagrammRahmen
              ladend={zeitreihe.isLoading}
              fehler={zeitreihe.error}
              leer={!zeitreihe.data || zeitreihe.data.length === 0}
            >
              <LinienDiagramm daten={zeitreihe.data ?? []} />
            </DiagrammRahmen>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Top Skills</CardTitle>
            <p className="text-xs text-muted-foreground">Klicken Sie einen Balken an.</p>
          </CardHeader>
          <CardContent>
            <DiagrammRahmen
              ladend={skills.isLoading}
              fehler={skills.error}
              leer={!skills.data || skills.data.length === 0}
            >
              <BalkenDiagramm
                daten={(skills.data ?? []).map((eintrag) => ({
                  beschriftung: eintrag.skill,
                  wert: eintrag.anzahl_jobs,
                  ziel: anzeigenLink({ skill: eintrag.skill }),
                }))}
                hoehe={320}
              />
            </DiagrammRahmen>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top Staedte</CardTitle>
            <p className="text-xs text-muted-foreground">Eine Stadt anklicken, um die Anzeigen zu sehen.</p>
          </CardHeader>
          <CardContent>
            <Liste
              ladend={staedte.isLoading}
              fehler={staedte.error}
              leer={!staedte.data || staedte.data.length === 0}
            >
              <ul className="divide-y">
                {(staedte.data ?? []).map((eintrag) => (
                  <li key={`${eintrag.stadt}-${eintrag.bundesland}`}>
                    <Link
                      href={anzeigenLink({ stadt: eintrag.stadt })}
                      className="-mx-2 flex items-center justify-between rounded-md px-2 py-2 text-sm transition-colors hover:bg-muted/60 focus:bg-muted/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <span>
                        {eintrag.stadt}
                        {eintrag.bundesland ? (
                          <span className="ml-2 text-xs text-muted-foreground">
                            {eintrag.bundesland}
                          </span>
                        ) : null}
                      </span>
                      <span className="kennzahl font-medium">
                        {formatZahl(eintrag.anzahl_jobs)}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </Liste>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Top Unternehmen</CardTitle>
            <p className="text-xs text-muted-foreground">Ein Unternehmen anklicken, um dessen Anzeigen zu sehen.</p>
          </CardHeader>
          <CardContent>
            <Liste
              ladend={unternehmen.isLoading}
              fehler={unternehmen.error}
              leer={!unternehmen.data || unternehmen.data.length === 0}
            >
              <ul className="divide-y">
                {(unternehmen.data ?? []).map((eintrag) => (
                  <li key={eintrag.unternehmen}>
                    <Link
                      href={anzeigenLink({ unternehmen: eintrag.unternehmen })}
                      className="-mx-2 flex items-center justify-between rounded-md px-2 py-2 text-sm transition-colors hover:bg-muted/60 focus:bg-muted/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <span>{eintrag.unternehmen}</span>
                      <span className="kennzahl font-medium">
                        {formatZahl(eintrag.anzahl_jobs)}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </Liste>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function KennzahlenKachel({
  titel,
  wert,
  ziel,
  ladend,
  fehler,
}: {
  titel: string;
  wert: string;
  ziel: string;
  ladend: boolean;
  fehler: unknown;
}) {
  return (
    <Link
      href={ziel}
      className="block rounded-lg transition-transform hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <Card>
        <CardHeader>
          <CardTitle>{titel}</CardTitle>
        </CardHeader>
        <CardContent>
          {ladend ? <Skeleton className="h-9 w-32" /> : null}
          {!ladend && fehler ? <p className="text-xs text-destructive">Fehler beim Laden</p> : null}
          {!ladend && !fehler ? <CardKennzahl>{wert}</CardKennzahl> : null}
        </CardContent>
      </Card>
    </Link>
  );
}

function DiagrammRahmen({
  ladend,
  fehler,
  leer,
  children,
}: {
  ladend: boolean;
  fehler: unknown;
  leer: boolean;
  children: React.ReactNode;
}) {
  if (ladend) return <Skeleton className="h-72 w-full" />;
  if (fehler) return <FehlerAnzeige meldung="Diagramm konnte nicht geladen werden." />;
  if (leer) return <LeererZustand titel="Noch keine Daten vorhanden" />;
  return <div className="h-72">{children}</div>;
}

function Liste({
  ladend,
  fehler,
  leer,
  children,
}: {
  ladend: boolean;
  fehler: unknown;
  leer: boolean;
  children: React.ReactNode;
}) {
  if (ladend) return <Skeleton className="h-64 w-full" />;
  if (fehler) return <FehlerAnzeige meldung="Liste konnte nicht geladen werden." />;
  if (leer) return <LeererZustand titel="Keine Eintraege vorhanden" />;
  return <>{children}</>;
}
