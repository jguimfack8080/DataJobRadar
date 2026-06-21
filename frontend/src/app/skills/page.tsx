'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FehlerAnzeige } from '@/components/ui/fehler-anzeige';
import { LeererZustand } from '@/components/ui/leerer-zustand';
import { Skeleton } from '@/components/ui/skeleton';
import { BalkenDiagramm } from '@/components/charts/balken-diagramm';
import { ApiFehler, holen } from '@/lib/api';
import type { SkillKennzahl } from '@/lib/api';
import { formatZahl } from '@/lib/utils';

const SEITENGROESSE = 50;

export default function SkillsSeite() {
  const [eintraege, setEintraege] = useState<SkillKennzahl[]>([]);
  const [offset, setOffset] = useState(0);
  const [ladend, setLadend] = useState<'init' | 'mehr' | null>('init');
  const [fehler, setFehler] = useState<string | null>(null);
  const [endeErreicht, setEndeErreicht] = useState(false);

  const seiteHolen = useCallback(async (startOffset: number) => {
    try {
      const ergebnis = await holen<SkillKennzahl[]>(
        `/skills?limit=${SEITENGROESSE}&offset=${startOffset}`
      );
      setEintraege((alt) => (startOffset === 0 ? ergebnis : [...alt, ...ergebnis]));
      if (ergebnis.length < SEITENGROESSE) setEndeErreicht(true);
      setFehler(null);
    } catch (problem) {
      if (problem instanceof ApiFehler) setFehler(problem.meldung);
      else if (problem instanceof Error) setFehler(problem.message);
      else setFehler('Unbekannter Fehler');
    } finally {
      setLadend(null);
    }
  }, []);

  useEffect(() => {
    void seiteHolen(0);
  }, [seiteHolen]);

  const mehrLaden = () => {
    const naechsterOffset = offset + SEITENGROESSE;
    setOffset(naechsterOffset);
    setLadend('mehr');
    void seiteHolen(naechsterOffset);
  };

  const diagrammDaten = eintraege.slice(0, 30).map((eintrag) => ({
    beschriftung: eintrag.skill,
    wert: eintrag.anzahl_jobs,
    ziel: `/anzeigen/?skill=${encodeURIComponent(eintrag.skill)}`,
  }));

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Skills</h1>
        <p className="text-sm text-muted-foreground">
          Gefragteste technische Faehigkeiten. Klicken Sie einen Balken oder eine Zeile an,
          um die zugehoerigen Anzeigen zu sehen.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Top 30 (visuell)</CardTitle>
        </CardHeader>
        <CardContent>
          {ladend === 'init' && <Skeleton className="h-96 w-full" />}
          {fehler && <FehlerAnzeige meldung={fehler} />}
          {ladend !== 'init' && !fehler && diagrammDaten.length > 0 && (
            <div className="h-96">
              <BalkenDiagramm
                daten={diagrammDaten}
                hoehe={384}
                beschriftungYAchse="Anzeigen"
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Alle Skills
            {eintraege.length > 0 ? (
              <span className="ml-2 text-xs text-muted-foreground">
                {eintraege.length} {endeErreicht ? 'angezeigt' : '(weitere verfuegbar)'}
              </span>
            ) : null}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {ladend === 'init' && <Skeleton className="h-64 w-full" />}
          {!ladend && !fehler && eintraege.length === 0 && (
            <LeererZustand titel="Noch keine Skill-Daten vorhanden." />
          )}
          {eintraege.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <table className="w-full table-auto text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wider text-muted-foreground">
                      <th className="px-3 py-2">Skill</th>
                      <th className="px-3 py-2 text-right">Anzeigen</th>
                      <th className="px-3 py-2 text-right">Nennungen</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {eintraege.map((eintrag) => (
                      <tr key={eintrag.skill} className="hover:bg-muted/40">
                        <td className="px-3 py-2">
                          <Link
                            href={`/anzeigen/?skill=${encodeURIComponent(eintrag.skill)}`}
                            className="block rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          >
                            {eintrag.skill}
                          </Link>
                        </td>
                        <td className="kennzahl px-3 py-2 text-right">
                          {formatZahl(eintrag.anzahl_jobs)}
                        </td>
                        <td className="kennzahl px-3 py-2 text-right">
                          {formatZahl(eintrag.anzahl)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-6 flex flex-col items-center gap-2">
                {!endeErreicht ? (
                  <button
                    type="button"
                    onClick={mehrLaden}
                    disabled={ladend === 'mehr'}
                    className="inline-flex items-center justify-center rounded-md border bg-card px-5 py-2 text-sm font-medium text-foreground shadow-card transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {ladend === 'mehr' ? 'Wird geladen...' : 'Mehr laden'}
                  </button>
                ) : (
                  <p className="text-xs text-muted-foreground">Alle Skills angezeigt.</p>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
