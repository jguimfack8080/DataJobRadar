import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const metadata = {
  title: 'Wiki - Data Job Radar Deutschland',
  description: 'Was ist diese Seite, wie nutzen Sie sie, und was bedeuten die Zahlen.',
};

export default function WikiSeite() {
  return (
    <article className="mx-auto flex max-w-4xl flex-col gap-8">
      <header className="space-y-3">
        <p className="text-xs uppercase tracking-wider text-muted-foreground">
          Wiki und Anleitung
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Data Job Radar Deutschland
        </h1>
        <p className="text-base text-muted-foreground">
          Ein Live-Marktradar fuer IT- und Data-Stellen in Deutschland. Mehrere Quellen
          - die offizielle Bundesagentur fuer Arbeit, Adzuna, The Muse, Remotive und Jobicy
          - werden zusammengefuehrt und auf Duplikate bereinigt. Sie sehen aktualisierte
          Statistiken zum Stellenmarkt: wer einstellt, was bezahlt wird, welche Skills
          gefragt sind und wo die Stellen verteilt sind.
        </p>
      </header>

      <KapitelKarte titel="Was ist das hier in einem Satz?">
        <p>
          Diese Seite sammelt mehrmals pro Tag automatisch alle relevanten IT- und
          Data-Stellenanzeigen aus fuenf Quellen, bereinigt sie Cross-Source und zeigt Ihnen die
          Trends, Top-Arbeitgeber, gefragtesten Skills und
          marktueblichen Gehaelter auf einen Blick.
        </p>
      </KapitelKarte>

      <KapitelKarte titel="Wofuer koennen Sie es nutzen?">
        <ul className="list-disc space-y-1.5 pl-5 text-sm">
          <li><span className="font-medium text-foreground">Jobsuche:</span> Filtern Sie nach Stadt, Skill, Vertragstyp und Gehalt und klicken Sie direkt zur Original-Anzeige.</li>
          <li><span className="font-medium text-foreground">Marktvergleich:</span> Was zahlen Unternehmen in Berlin gegenueber Muenchen? Wo ist die Nachfrage am hoechsten?</li>
          <li><span className="font-medium text-foreground">Gehaltscheck:</span> Liegt Ihr Wunschgehalt im Marktrahmen fuer Ihre Kategorie und Region?</li>
          <li><span className="font-medium text-foreground">Skill-Planung:</span> Welche Technologien tauchen am haeufigsten in Stellenausschreibungen auf?</li>
          <li><span className="font-medium text-foreground">Recruiting:</span> Welche Konkurrenz gibt es fuer Ihre offenen Stellen, wo finden Sie aehnliche Profile?</li>
        </ul>
      </KapitelKarte>

      <KapitelKarte titel="So nutzen Sie die einzelnen Seiten">
        <Anleitung
          titel="Uebersicht"
          zweck="Schneller Blick auf die wichtigsten Marktzahlen."
          schritte={[
            'Die vier Kacheln oben zeigen aktive Anzeigen, Unternehmen, Standorte und das mittlere Gehalt.',
            'Das Liniendiagramm zeigt, wie viele neue Anzeigen in den letzten 30 Tagen veroeffentlicht wurden.',
            'Das Balkendiagramm "Top Skills" zeigt die haeufigsten Anforderungen.',
            'Die beiden unteren Listen zeigen die staerksten Staedte und Unternehmen.',
          ]}
        />
        <Anleitung
          titel="Stellenanzeigen"
          zweck="Konkrete Stellen suchen, speichern und direkt zur Original-Anzeige springen."
          schritte={[
            'Geben Sie oben einen Suchbegriff ein (Titel oder Unternehmen) und klicken Sie "Filter anwenden".',
            'Direkt unter den Eingabefeldern koennen Sie die Datenquellen auswaehlen (Bundesagentur, Adzuna, The Muse, Remotive, Jobicy). Mehrfachauswahl, ODER-Verknuepfung.',
            'Mit "Mehr Filter" oeffnen Sie die volle Filtersuite: Bundesland, Kategorie, Vertragstyp, Vertragszeit, Gehaltsspanne, Datumsbereich, Skills.',
            'Skills sind Mehrfachauswahl mit UND-Verknuepfung: Wer "Python" und "AWS" anklickt, sieht nur Anzeigen mit beiden.',
            'Klicken Sie den Titel einer Anzeige an, um sie bei der jeweiligen Quelle in einem neuen Tab zu oeffnen. Die Anzeige erhaelt danach das Badge "Gesehen" (grau).',
            'Swipe nach rechts auf einer Karte (Touch oder Maus), um sie sofort als Beworben zu markieren. Ein gruener Hintergrund erscheint waehrend der Geste und bestaetigt die Aktion.',
            'Swipe nach links, um eine Anzeige zu speichern oder aus den Gespeicherten zu entfernen. Ein cyaner Hintergrund zeigt die Aktion an.',
            'Das Lesezeichen-Symbol rechts auf jeder Karte speichert die Anzeige alternativ per Klick. Gespeicherte Anzeigen sind mit einem cyan Badge markiert.',
            'Sobald eine Anzeige gespeichert ist, erscheint der Button "Beworben", um die Bewerbung alternativ per Klick zu vermerken (gruenes Badge).',
            'Der Schalter "Nur Neue" in der Ergebnis-Kopfzeile blendet alle bereits gesehenen Anzeigen aus.',
            'Unten erscheint "Mehr laden", solange weitere Treffer verfuegbar sind.',
            'Mit "Zuruecksetzen" loeschen Sie alle Filter auf einen Klick.',
          ]}
        />
        <Anleitung
          titel="Gespeicherte Stellen"
          zweck="Gespeicherte und beworbene Anzeigen auf einen Blick verwalten."
          schritte={[
            'Die Seite ist ueber "Gespeichert" in der linken Navigation erreichbar. Das Lesezeichen-Symbol zeigt die Anzahl gespeicherter Stellen.',
            'Zwei Bereiche: "Gespeichert" (Anzeigen zum spaeteren Bewerben) und "Beworben" (bereits beworbene Stellen).',
            'Klicken Sie auf den Titel, um die Original-Anzeige direkt zu oeffnen.',
            'Mit "Beworben" verschieben Sie eine gespeicherte Anzeige in den Bereich "Beworben".',
            'Mit dem Papierkorb-Symbol entfernen Sie eine Anzeige vollstaendig aus dem lokalen Speicher.',
            'Alle Daten liegen ausschliesslich in Ihrem Browser (LocalStorage). Sie werden nicht uebertragen oder synchronisiert.',
            'Hinweis: Da Anzeigen bei den Quellen jederzeit ablaufen koennen, empfehlen wir, sich zeitnah zu bewerben.',
          ]}
        />
        <Anleitung
          titel="Skills"
          zweck="Welche Technologien werden am haeufigsten gefordert."
          schritte={[
            'Das Balkendiagramm zeigt die Top-30-Skills nach Anzahl der Anzeigen, in denen sie vorkommen.',
            'Tipp: Skills tauchen oft in Kombination auf; sehen Sie unter Stellenanzeigen, indem Sie mehrere Skills auswaehlen, wie viele Anzeigen gleichzeitig diese fordern.',
          ]}
        />
        <Anleitung
          titel="Unternehmen"
          zweck="Wer stellt am meisten ein."
          schritte={[
            'Die Tabelle ist nach Anzahl offener Anzeigen sortiert.',
            'Die Spalte "Mittleres Gehalt" wird nur dann gefuellt, wenn der Arbeitgeber selbst Gehaelter in seinen Anzeigen veroeffentlicht.',
          ]}
        />
        <Anleitung
          titel="Staedte"
          zweck="Regionale Verteilung der Nachfrage."
          schritte={[
            'Top 20 Staedte nach Anzahl der Anzeigen. Berlin, Muenchen, Hamburg und Koeln sind ueblicherweise vorne.',
          ]}
        />
        <Anleitung
          titel="Trends"
          zweck="Wie sich der Markt ueber die Zeit und nach Region entwickelt."
          schritte={[
            'Die Zeitreihe zeigt 60 Tage Neuveroeffentlichungen.',
            'Die Gehaltsverteilung laesst sich nach Kategorie, Stadt oder Bundesland gruppieren. Sie zeigt die 25%-, 50%- und 75%-Quantile.',
            'Lese-Hilfe: das mittlere 50% der Loehne (vom unteren Ende des Balkens bis zum oberen Ende) ist die typische Spanne fuer diese Gruppe.',
          ]}
        />
      </KapitelKarte>

      <KapitelKarte titel="Was bedeuten die Zahlen?">
        <ul className="space-y-2 text-sm">
          <li><span className="font-medium text-foreground">Aktive Anzeigen:</span> Aktuelle Stellen aus allen fuenf Quellen mit Bezug zu Deutschland. Eine Stelle, die in mehreren Quellen oder mehrfach am Tag erscheint, wird nur einmal gezaehlt.</li>
          <li><span className="font-medium text-foreground">Gehalt:</span> Wenn die Anzeige eine Spanne hat, nehmen wir den Mittelwert. Steht nur ein Wert in der Anzeige, nutzen wir genau diesen. Ohne Angabe wird die Anzeige nicht in Gehaltsstatistiken einberechnet.</li>
          <li><span className="font-medium text-foreground">Skills:</span> Werden aus dem Beschreibungstext der Anzeige automatisch erkannt. Nicht jeder Skill, der vorkommt, wird zwingend als zwingende Anforderung verstanden.</li>
          <li><span className="font-medium text-foreground">Stadt und Bundesland:</span> Stammen aus den Geo-Angaben der Anzeige. Anzeigen ohne klare Ortsangabe landen in "Deutschland / unbekannt".</li>
        </ul>
      </KapitelKarte>

      <KapitelKarte titel="Wie aktuell sind die Daten?">
        <p>
          Die Pipeline laeuft taeglich automatisch und holt alle neuen Anzeigen. Die juengste
          Aktualisierung sehen Sie auf der Uebersichtsseite unter "spaeteste Anzeige".
          Anzeigen, die bei der Quelle nicht mehr verfuegbar sind, bleiben aus historischen Gruenden
          weiterhin sichtbar, koennen aber nicht mehr beworben werden; deshalb empfehlen wir,
          den direkten Link zu pruefen.
        </p>
      </KapitelKarte>

      <KapitelKarte titel="Datenquellen und Lizenz">
        <p className="mb-3 text-sm">
          Daten stammen aus fuenf oeffentlichen Quellen. Jede Stelle verlinkt direkt auf
          das Original bei der jeweiligen Quelle. Diese Seite ist kostenfrei nutzbar und
          gibt die Daten unveraendert wieder.
        </p>
        <ul className="space-y-2 text-sm">
          <li>
            <span className="font-medium text-foreground">Bundesagentur fuer Arbeit</span> -
            offizielle deutsche Jobboerse, hoechste Datenqualitaet.{' '}
            <a
              href="https://www.arbeitsagentur.de/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent underline-offset-4 hover:underline"
            >
              arbeitsagentur.de
            </a>
          </li>
          <li>
            <span className="font-medium text-foreground">Adzuna</span> - breite Marktabdeckung
            mit aggregierten Stellen aus vielen Boersen.{' '}
            <a
              href="https://developer.adzuna.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent underline-offset-4 hover:underline"
            >
              developer.adzuna.com
            </a>
          </li>
          <li>
            <span className="font-medium text-foreground">The Muse</span> - kuratierte
            Tech-Stellen, ueberwiegend international.{' '}
            <a
              href="https://www.themuse.com/developers/api"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent underline-offset-4 hover:underline"
            >
              themuse.com/developers
            </a>
          </li>
          <li>
            <span className="font-medium text-foreground">Remotive</span> - Remote-Stellen,
            Filter auf DE/EU/Worldwide.{' '}
            <a
              href="https://remotive.com/api-documentation"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent underline-offset-4 hover:underline"
            >
              remotive.com
            </a>
          </li>
          <li>
            <span className="font-medium text-foreground">Jobicy</span> - Remote-Stellen, Filter
            auf DE/EU/Worldwide.{' '}
            <a
              href="https://jobicy.com/jobs-rss-feed"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent underline-offset-4 hover:underline"
            >
              jobicy.com
            </a>
          </li>
        </ul>
        <p className="mt-3 text-xs text-muted-foreground">
          Cross-Source-Deduplizierung: erscheint dieselbe Stelle in mehreren Quellen, wird sie
          genau einmal angezeigt. Die Quelle mit der hoechsten Datenqualitaet wird behalten
          (Reihenfolge: Bundesagentur, Adzuna, The Muse, Remotive, Jobicy).
        </p>
      </KapitelKarte>

      <KapitelKarte titel="Grenzen und Hinweise">
        <ul className="list-disc space-y-1.5 pl-5 text-sm">
          <li>Manche Anzeigen enthalten kein Gehalt; diese tauchen in den Gehaltsstatistiken nicht auf.</li>
          <li>Die Skill-Erkennung ist regelbasiert und kann gelegentlich Fehltreffer produzieren (zum Beispiel "R" als Programmiersprache erkennen, obwohl in der Anzeige nur ein Buchstabe gemeint ist).</li>
          <li>Sehr kleine Orte erscheinen oft als "Deutschland", weil die Original-Anzeige keine genauere Angabe enthaelt.</li>
          <li>Es werden Stellen aus den fuenf integrierten Quellen beruecksichtigt; bei Remote-Boersen (Remotive, Jobicy, The Muse) wird zusaetzlich auf Standorte Germany, Europe, EU, EMEA, Worldwide oder Anywhere gefiltert.</li>
        </ul>
      </KapitelKarte>

      <KapitelKarte titel="Wie die Daten verarbeitet werden">
        <Diagramm
          quelle="/diagramme/datenfluss.svg"
          alt="Fuenf Quellen -> Ingestion -> Bronze -> Silver -> Gold -> API -> Dashboard"
          beschriftung="Von fuenf Quellen bis zu diesem Dashboard: vier automatische Laeufe pro Tag mit Cross-Source-Deduplizierung."
        />
      </KapitelKarte>

      <KapitelKarte titel="Technische Architektur (fuer Interessierte)">
        <p className="text-sm">
          Wer es genauer wissen will: hier die wichtigsten Diagramme der Plattform. Sie sind
          jeweils einzeln aufklickbar und auch im{' '}
          <a
            href="https://github.com/jguimfack8080/DataJobRadar"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-accent underline-offset-4 hover:underline"
          >
            Repository
          </a>{' '}
          verfuegbar.
        </p>
        <div className="mt-4 space-y-6">
          <Diagramm
            quelle="/diagramme/architektur.svg"
            alt="Systemarchitektur"
            beschriftung="Systemarchitektur: Schichten und Komponenten"
          />
          <Diagramm
            quelle="/diagramme/medallion.svg"
            alt="Medallion Architecture"
            beschriftung="Medallion: Bronze, Silver, Gold - wie die Daten veredelt werden"
          />
          <Diagramm
            quelle="/diagramme/airflow_dag.svg"
            alt="Airflow DAG"
            beschriftung="Taeglicher automatischer Ablauf der Datenpipeline"
          />
          <Diagramm
            quelle="/diagramme/datenmodell.svg"
            alt="Sternschema"
            beschriftung="Datenmodell: Fakten- und Dimensionstabellen"
          />
          <Diagramm
            quelle="/diagramme/deployment.svg"
            alt="Deployment-Topologie"
            beschriftung="Wie die Anwendung in Produktion laeuft"
          />
        </div>
      </KapitelKarte>
    </article>
  );
}

function KapitelKarte({ titel, children }: { titel: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground">{titel}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm leading-relaxed text-muted-foreground">
        {children}
      </CardContent>
    </Card>
  );
}

function Anleitung({
  titel,
  zweck,
  schritte,
}: {
  titel: string;
  zweck: string;
  schritte: string[];
}) {
  return (
    <div className="mb-5 rounded-lg border bg-muted/30 p-4">
      <p className="text-sm font-semibold text-foreground">{titel}</p>
      <p className="mt-1 text-xs italic text-muted-foreground">Zweck: {zweck}</p>
      <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm">
        {schritte.map((eintrag, index) => (
          <li key={`${titel}-${index}`}>{eintrag}</li>
        ))}
      </ol>
    </div>
  );
}

function Diagramm({
  quelle,
  alt,
  beschriftung,
}: {
  quelle: string;
  alt: string;
  beschriftung: string;
}) {
  return (
    <figure className="space-y-2">
      <div className="overflow-hidden rounded-lg border bg-white p-3">
        <img src={quelle} alt={alt} className="block h-auto w-full" loading="lazy" />
      </div>
      <figcaption className="text-xs text-muted-foreground">{beschriftung}</figcaption>
    </figure>
  );
}
