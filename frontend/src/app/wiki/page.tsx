import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const metadata = {
  title: 'Wiki - Data Job Radar Deutschland',
  description: 'Hintergrund, Architektur und Technik-Stack des Projekts.',
};

export default function WikiSeite() {
  return (
    <article className="mx-auto flex max-w-4xl flex-col gap-8">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-wider text-muted-foreground">
          Projektwiki
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Data Job Radar Deutschland
        </h1>
        <p className="text-base text-muted-foreground">
          Eine vollstaendige Data-Engineering-Plattform fuer den deutschen IT-Arbeitsmarkt.
          Von der Adzuna-API-Ingestion ueber ein Bronze-Silver-Gold Data Lake bis zum
          Dashboard, das Sie gerade sehen.
        </p>
      </header>

      <KapitelKarte titel="Worum es geht">
        <p>
          Das Projekt sammelt taeglich Stellenanzeigen aus dem deutschen IT-Markt,
          bereinigt und modelliert sie und macht die Ergebnisse als Statistiken,
          Skill-Trends und Gehaltsverteilungen sichtbar. Es ist als Portfolio-Projekt
          fuer Data-Engineering-Bewerbungen entstanden und folgt durchgaengig produktiven
          Mustern.
        </p>
      </KapitelKarte>

      <KapitelKarte titel="Systemarchitektur (Diagramm)">
        <Diagramm
          quelle="/diagramme/architektur.svg"
          alt="Schwarz-weisse Systemarchitektur mit Ingestion, Bronze-Silver-Gold, dbt, DuckDB, FastAPI und Dashboard"
          beschriftung="Schichten und Verantwortlichkeiten im Ueberblick"
        />
      </KapitelKarte>

      <KapitelKarte titel="Architektur in Worten">
        <ul className="space-y-1.5 text-sm">
          <li><span className="font-medium text-foreground">Ingestion:</span> Adzuna-API mit httpx und tenacity, idempotent, schema-validiert, mit Quarantaene fuer ungueltige Datensaetze.</li>
          <li><span className="font-medium text-foreground">Bronze:</span> Roh-Parquet partitioniert nach Datum und Kategorie, Zstd-komprimiert.</li>
          <li><span className="font-medium text-foreground">Silver:</span> Bereinigung, Deduplizierung anhand der Adzuna-ID und Skill-Extraktion ueber eine konfigurierbare Taxonomie.</li>
          <li><span className="font-medium text-foreground">Gold:</span> Sternschema (fact_jobs, fact_skills, dim_company, dim_location, dim_date) materialisiert von dbt Core.</li>
          <li><span className="font-medium text-foreground">Warehouse:</span> DuckDB als prozessinternes OLAP-Werkzeug ohne separaten Datenbankserver.</li>
          <li><span className="font-medium text-foreground">API:</span> FastAPI mit Pydantic v2, Keyset-Pagination, konsistentes Fehlerschema, In-Memory-Cache und Rate Limiting.</li>
          <li><span className="font-medium text-foreground">Dashboard:</span> Next.js mit statischem Export, vom Backend ausgeliefert.</li>
          <li><span className="font-medium text-foreground">Orchestrierung:</span> Apache Airflow mit LocalExecutor.</li>
        </ul>
      </KapitelKarte>

      <KapitelKarte titel="Medallion-Schichten (Diagramm)">
        <Diagramm
          quelle="/diagramme/medallion.svg"
          alt="Bronze, Silver und Gold als drei nebeneinander stehende Spalten mit jeweiligen Aufgaben"
          beschriftung="Wie die Daten vom Roh-Zustand bis zur Analyse veredelt werden"
        />
      </KapitelKarte>

      <KapitelKarte titel="Datenfluss (Diagramm)">
        <Diagramm
          quelle="/diagramme/datenfluss.svg"
          alt="Pfeile von Adzuna ueber Ingestion, Bronze, Silver, Gold zu API und Dashboard"
          beschriftung="Adzuna bis Dashboard auf einer Linie"
        />
      </KapitelKarte>

      <KapitelKarte titel="Datenfluss in Worten">
        <ol className="list-decimal space-y-1.5 pl-5 text-sm">
          <li>Airflow triggert taeglich einen Lauf.</li>
          <li>Der Adzuna-Client ruft seitenweise Stellenangebote ab, mit exponentiellem Backoff bei Fehlern und Quota-Erkennung.</li>
          <li>Jeder Treffer wird gegen ein Pydantic-Schema gepruefft. Verletzungen landen in einer Quarantaene-Datei, nicht im stillen Loeschmuelleimer.</li>
          <li>Bronze speichert die validierten Roh-Daten unveraendert als Parquet.</li>
          <li>Silver wendet eine DuckDB-Transformation an: Normalisierung, Deduplizierung, Skill-Extraktion ueber eine erweiterbare Taxonomie.</li>
          <li>dbt Core baut darauf das Sternschema mit Tests fuer Eindeutigkeit, Nicht-Null-Bedingungen, referenzielle Integritaet und erlaubte Werte.</li>
          <li>Das Backend liest read-only aus DuckDB und liefert die typisierten Antworten an dieses Dashboard.</li>
        </ol>
      </KapitelKarte>

      <KapitelKarte titel="Airflow-DAG (Diagramm)">
        <Diagramm
          quelle="/diagramme/airflow_dag.svg"
          alt="Sechs Tasks von ingestion_lauf bis dbt_test mit Pfeilen verbunden"
          beschriftung="arbeitsmarkt_data_pipeline taeglich um 06:00 UTC"
        />
      </KapitelKarte>

      <KapitelKarte titel="Datenmodell als Sternschema (Diagramm)">
        <Diagramm
          quelle="/diagramme/datenmodell.svg"
          alt="Faktentabelle fact_jobs in der Mitte, dim_company, dim_location, dim_date und fact_skills daran"
          beschriftung="Klassisches dimensionales Modell, materialisiert von dbt"
        />
      </KapitelKarte>

      <KapitelKarte titel="Datenmodell in Worten">
        <ul className="space-y-1.5 text-sm">
          <li><span className="font-mono text-foreground">fact_jobs</span>: eine Zeile pro Stellenanzeige mit Fremdschluesseln auf Unternehmen und Standort.</li>
          <li><span className="font-mono text-foreground">fact_skills</span>: eine Zeile pro Skill je Anzeige (Many-to-Many) mit Gewichtung.</li>
          <li><span className="font-mono text-foreground">dim_company</span>: normalisierte Unternehmen mit Surrogatschluessel.</li>
          <li><span className="font-mono text-foreground">dim_location</span>: Stadt, Bundesland, Region.</li>
          <li><span className="font-mono text-foreground">dim_date</span>: klassische Datumsdimension fuer Zeitreihen.</li>
        </ul>
      </KapitelKarte>

      <KapitelKarte titel="Deployment-Topologie (Diagramm)">
        <Diagramm
          quelle="/diagramme/deployment.svg"
          alt="Endnutzer, Host-Nginx und der Docker-Stack mit Backend, Airflow, Postgres und Volumes"
          beschriftung="Einer extern erreichbarer Port, alles andere auf Loopback"
        />
      </KapitelKarte>

      <KapitelKarte titel="Eingesetzte Technologien">
        <div className="grid gap-3 sm:grid-cols-2">
          <TechBlock kategorie="Sprachen" eintraege={['Python 3.12', 'TypeScript', 'SQL']} />
          <TechBlock kategorie="Pipeline" eintraege={['Apache Airflow', 'dbt Core', 'DuckDB', 'pyarrow']} />
          <TechBlock kategorie="Backend" eintraege={['FastAPI', 'Pydantic v2', 'Uvicorn', 'httpx', 'tenacity', 'structlog']} />
          <TechBlock kategorie="Frontend" eintraege={['Next.js 14 RSC', 'Tailwind CSS', 'Recharts', 'SWR', 'Shadcn-UI-Muster']} />
          <TechBlock kategorie="Infrastruktur" eintraege={['Docker Compose', 'Nginx Reverse Proxy', 'Postgres (nur Airflow Metadaten)']} />
          <TechBlock kategorie="Qualitaet" eintraege={['pytest', 'ruff', 'mypy', 'dbt tests']} />
        </div>
      </KapitelKarte>

      <KapitelKarte titel="Was das Projekt besonders macht">
        <ul className="space-y-1.5 text-sm">
          <li>End-to-End Verantwortung: Ingestion, Storage, Transformation, Warehouse, API, UI und Deployment in einem Repository.</li>
          <li>Produktive Muster statt Tutorial-Code: idempotente Pipeline, Backoff mit Jitter, Schema-Quarantaene, strukturierte Logs mit Korrelationskennung.</li>
          <li>Pragmatische Ressourcenoptimierung: DuckDB statt Postgres-Warehouse, LocalExecutor statt Celery, statischer Frontend-Export statt separatem Node-Server.</li>
          <li>Datenqualitaet als Pflicht: dbt-Tests fuer Eindeutigkeit, referenzielle Integritaet und erlaubte Werte; Quarantaene-Zaehler im Lauf-Bericht.</li>
          <li>Sicherheitsbewusst: Geheimnisse nur ueber Environment-Variablen, Rate Limiting, CORS-Whitelist, konsistentes Fehlerformat ohne Preisgabe interner Details.</li>
          <li>Realer deutscher Markt: 3.000+ aktive Anzeigen, 700+ Unternehmen, Gehaltsstatistiken nach Bundesland und Kategorie.</li>
        </ul>
      </KapitelKarte>

      <KapitelKarte titel="Bekannte Grenzen und naechste Schritte">
        <ul className="space-y-1.5 text-sm">
          <li>Aktuell ausschliesslich Adzuna als Quelle. Weitere Quellen (StepStone, Indeed) liessen sich als zusaetzliche Ingestion-Adapter ergaenzen.</li>
          <li>Batch-Pipeline, kein Streaming. Eine spaetere Erweiterung um Kafka oder Kinesis ist denkbar, ist aber bei den taeglichen Volumen nicht noetig.</li>
          <li>Single-Node DuckDB: ausreichend fuer den aktuellen Datenumfang, fuer mehrere Mandanten waere ein dediziertes Warehouse sinnvoller.</li>
          <li>Skill-Extraktion ueber Regex-Taxonomie: einfach und nachvollziehbar, koennte fuer hoehere Praezision durch ein NER-Modell oder LLM ergaenzt werden.</li>
        </ul>
      </KapitelKarte>

      <KapitelKarte titel="Quellcode und Lizenz">
        <p className="text-sm">
          Vollstaendiger Quellcode auf GitHub:{' '}
          <a
            href="https://github.com/jguimfack8080/DataJobRadar"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-accent underline-offset-4 hover:underline"
          >
            jguimfack8080/DataJobRadar
          </a>
          . Das Repository enthaelt eine ausfuehrliche README mit Setup-Anleitung,
          Architektur-Entscheidungen (ADRs) und mehreren Diagrammen.
        </p>
      </KapitelKarte>

      <footer className="border-t pt-6 text-xs text-muted-foreground">
        Datenquelle: Adzuna API (Land: de). Diese Plattform ist ein nicht-kommerzielles
        Portfolio-Projekt. Jede Stellenanzeige verlinkt direkt auf das Original bei
        Adzuna.
      </footer>
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

function TechBlock({ kategorie, eintraege }: { kategorie: string; eintraege: string[] }) {
  return (
    <div className="rounded-lg border bg-muted/30 p-3">
      <p className="text-xs uppercase tracking-wider text-muted-foreground">{kategorie}</p>
      <p className="mt-1 flex flex-wrap gap-1.5">
        {eintraege.map((eintrag) => (
          <span
            key={eintrag}
            className="rounded-full border bg-card px-2 py-0.5 text-xs text-foreground"
          >
            {eintrag}
          </span>
        ))}
      </p>
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
