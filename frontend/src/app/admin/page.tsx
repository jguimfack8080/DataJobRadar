'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const API = '/api/v1/admin/visites-stats';
const TOKEN_KEY = 'djr_admin_token';
const REFRESH_MS = 30_000;

interface Eintrag {
  name: string;
  anzahl: number;
}

interface Besuch {
  zeitpunkt: string;
  ip: string;
  geo: string;
  pfad: string;
  status: string;
  ua: string;
  referrer: string;
}

interface Stats {
  gesamt: number;
  eindeutige_ips: number;
  heute: number;
  diese_woche: number;
  diesen_monat: number;
  pro_tag: { tag: string; anzahl: number }[];
  top_laender: Eintrag[];
  top_staedte: Eintrag[];
  top_pfade: Eintrag[];
  top_referrer: Eintrag[];
  top_isps: Eintrag[];
  status_verteilung: Eintrag[];
  geraete: Eintrag[];
  letzte_besuche: Besuch[];
}

function kuerzenDatum(tag: string): string {
  const parts = tag.split('-');
  if (parts.length !== 3) return tag;
  return `${parts[2]}.${parts[1]}`;
}

function formatN(n: number): string {
  return n.toLocaleString('de-DE');
}

function statusFarbe(s: string): string {
  if (s.startsWith('2')) return '#22c55e';
  if (s.startsWith('3')) return '#3b82f6';
  if (s.startsWith('4')) return '#f59e0b';
  if (s.startsWith('5')) return '#ef4444';
  return '#6b7280';
}

function KpiKarte({
  titel,
  wert,
  sub,
  akzent,
}: {
  titel: string;
  wert: string | number;
  sub?: string;
  akzent?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border p-5 shadow-card ${
        akzent ? 'border-accent/40 bg-accent/5' : 'bg-card'
      }`}
    >
      <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground">{titel}</p>
      <p className={`mt-2 text-3xl font-bold tabular-nums ${akzent ? 'text-accent' : ''}`}>
        {typeof wert === 'number' ? formatN(wert) : wert}
      </p>
      {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
    </div>
  );
}

function Prozentbalken({ wert, max }: { wert: number; max: number }) {
  const pct = max > 0 ? Math.round((wert / max) * 100) : 0;
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-accent transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-8 text-right text-xs tabular-nums text-muted-foreground">{pct}%</span>
    </div>
  );
}

function LoginMaske({ onToken }: { onToken: (t: string) => void }) {
  const [wert, setWert] = useState('');
  const [fehler, setFehler] = useState('');
  const [laden, setLaden] = useState(false);

  const absenden = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wert.trim()) return;
    setLaden(true);
    setFehler('');
    try {
      const r = await fetch(`${API}?token=${encodeURIComponent(wert.trim())}`);
      if (r.ok) {
        localStorage.setItem(TOKEN_KEY, wert.trim());
        onToken(wert.trim());
      } else if (r.status === 403) {
        setFehler('Token ungueltig. Bitte pruefen.');
      } else {
        setFehler(`Fehler ${r.status}`);
      }
    } catch {
      setFehler('Verbindungsfehler.');
    } finally {
      setLaden(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
      <div className="w-full max-w-sm rounded-2xl border bg-card p-8 shadow-card">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10">
            <svg
              className="h-6 w-6 text-accent"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
              />
            </svg>
          </div>
          <h1 className="text-lg font-semibold">Admin-Zugang</h1>
          <p className="mt-1 text-sm text-muted-foreground">Token eingeben</p>
        </div>
        <form onSubmit={absenden} className="flex flex-col gap-4">
          <input
            type="password"
            value={wert}
            onChange={(e) => setWert(e.target.value)}
            placeholder="Admin-Token"
            autoFocus
            className="rounded-lg border bg-background px-4 py-2.5 text-sm outline-none ring-accent/50 focus:ring-2"
          />
          {fehler && <p className="text-xs text-destructive">{fehler}</p>}
          <button
            type="submit"
            disabled={laden}
            className="rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-accent-foreground transition-opacity disabled:opacity-50"
          >
            {laden ? 'Pruefen...' : 'Anmelden'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function AdminSeite() {
  const [token, setToken] = useState<string | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [laden, setLaden] = useState(false);
  const [fehler, setFehler] = useState('');
  const [letzteAktualisierung, setLetzteAktualisierung] = useState('');
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const gespeichert = localStorage.getItem(TOKEN_KEY);
    if (gespeichert) setToken(gespeichert);
  }, []);

  const laden_daten = useCallback(
    async (t: string) => {
      setLaden(true);
      setFehler('');
      try {
        const r = await fetch(`${API}?token=${encodeURIComponent(t)}`);
        if (r.status === 403) {
          localStorage.removeItem(TOKEN_KEY);
          setToken(null);
          return;
        }
        if (!r.ok) {
          setFehler(`Fehler ${r.status}`);
          return;
        }
        const d: Stats = await r.json();
        setStats(d);
        setLetzteAktualisierung(new Date().toLocaleTimeString('de-DE'));
      } catch {
        setFehler('Verbindungsfehler.');
      } finally {
        setLaden(false);
      }
    },
    []
  );

  useEffect(() => {
    if (!token) return;
    laden_daten(token);
    intervalRef.current = setInterval(() => laden_daten(token), REFRESH_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [token, laden_daten]);

  if (!token) return <LoginMaske onToken={setToken} />;

  return (
    <div className="space-y-8 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Besucherstatistiken</h1>
          <p className="text-sm text-muted-foreground">
            Echtzeit-Uebersicht aller Aufrufe auf Data Job Radar Deutschland
          </p>
        </div>
        <div className="flex items-center gap-3">
          {letzteAktualisierung && (
            <span className="text-xs text-muted-foreground">
              Aktualisiert: {letzteAktualisierung}
            </span>
          )}
          <button
            onClick={() => token && laden_daten(token)}
            disabled={laden}
            className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-muted disabled:opacity-50"
          >
            <svg
              className={`h-3.5 w-3.5 ${laden ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
              />
            </svg>
            Neu laden
          </button>
          <button
            onClick={() => {
              localStorage.removeItem(TOKEN_KEY);
              setToken(null);
            }}
            className="rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted"
          >
            Abmelden
          </button>
        </div>
      </div>

      {fehler && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {fehler}
        </div>
      )}

      {!stats && laden && (
        <div className="flex items-center justify-center py-20 text-muted-foreground text-sm">
          Daten werden geladen...
        </div>
      )}

      {stats && (
        <>
          <section className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            <KpiKarte titel="Besuche gesamt" wert={stats.gesamt} akzent />
            <KpiKarte titel="Eindeutige IPs" wert={stats.eindeutige_ips} />
            <KpiKarte titel="Heute" wert={stats.heute} />
            <KpiKarte titel="Diese Woche" wert={stats.diese_woche} />
            <KpiKarte titel="Diesen Monat" wert={stats.diesen_monat} />
          </section>

          <section>
            <div className="rounded-xl border bg-card p-5 shadow-card">
              <h2 className="mb-4 text-sm font-semibold">Besuche pro Tag (letzte 30 Tage)</h2>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart
                  data={stats.pro_tag}
                  margin={{ top: 8, right: 8, left: 0, bottom: 4 }}
                >
                  <defs>
                    <linearGradient id="admin-akzent" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    stroke="hsl(var(--border))"
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="tag"
                    tickFormatter={kuerzenDatum}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                    tickLine={false}
                    axisLine={{ stroke: 'hsl(var(--border))' }}
                    interval={4}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    width={32}
                  />
                  <Tooltip
                    cursor={{ stroke: 'hsl(var(--border))' }}
                    contentStyle={{
                      background: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(v) => [formatN(Number(v)), 'Besuche']}
                    labelStyle={{ color: 'hsl(var(--foreground))' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="anzahl"
                    stroke="hsl(var(--accent))"
                    strokeWidth={2}
                    fill="url(#admin-akzent)"
                    animationDuration={400}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-xl border bg-card p-5 shadow-card">
              <h2 className="mb-4 text-sm font-semibold">Top-Laender</h2>
              {stats.top_laender.length === 0 ? (
                <p className="text-sm text-muted-foreground">Keine Daten</p>
              ) : (
                <div className="space-y-2.5">
                  {stats.top_laender.map((e) => (
                    <div key={e.name} className="flex items-center justify-between gap-3">
                      <span className="w-36 truncate text-sm" title={e.name}>
                        {e.name}
                      </span>
                      <Prozentbalken wert={e.anzahl} max={stats.top_laender[0]?.anzahl ?? 1} />
                      <span className="w-10 text-right text-sm tabular-nums font-medium">
                        {formatN(e.anzahl)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-xl border bg-card p-5 shadow-card">
              <h2 className="mb-4 text-sm font-semibold">Top-Seiten</h2>
              {stats.top_pfade.length === 0 ? (
                <p className="text-sm text-muted-foreground">Keine Daten</p>
              ) : (
                <div className="space-y-2.5">
                  {stats.top_pfade.map((e) => (
                    <div key={e.name} className="flex items-center justify-between gap-3">
                      <span className="w-36 truncate text-sm font-mono text-xs" title={e.name}>
                        {e.name}
                      </span>
                      <Prozentbalken wert={e.anzahl} max={stats.top_pfade[0]?.anzahl ?? 1} />
                      <span className="w-10 text-right text-sm tabular-nums font-medium">
                        {formatN(e.anzahl)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-xl border bg-card p-5 shadow-card">
              <h2 className="mb-4 text-sm font-semibold">Top-Staedte</h2>
              {stats.top_staedte.length === 0 ? (
                <p className="text-sm text-muted-foreground">Keine Daten</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart
                    data={stats.top_staedte.slice(0, 8).map((e) => ({
                      beschriftung: e.name.length > 12 ? e.name.slice(0, 12) + '...' : e.name,
                      wert: e.anzahl,
                    }))}
                    margin={{ top: 8, right: 8, left: 0, bottom: 4 }}
                  >
                    <CartesianGrid
                      stroke="hsl(var(--border))"
                      strokeDasharray="3 3"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="beschriftung"
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: 'hsl(var(--border))' }}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                      width={32}
                    />
                    <Tooltip
                      cursor={{ fill: 'hsl(var(--muted))' }}
                      contentStyle={{
                        background: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                      formatter={(v) => [formatN(Number(v)), 'Besuche']}
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                    />
                    <Bar
                      dataKey="wert"
                      fill="hsl(var(--accent))"
                      radius={[5, 5, 0, 0]}
                      animationDuration={400}
                    />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="rounded-xl border bg-card p-5 shadow-card">
              <h2 className="mb-4 text-sm font-semibold">Geraete</h2>
              {stats.geraete.length === 0 ? (
                <p className="text-sm text-muted-foreground">Keine Daten</p>
              ) : (
                <div className="space-y-2.5">
                  {stats.geraete.map((e) => (
                    <div key={e.name} className="flex items-center justify-between gap-3">
                      <span className="w-36 truncate text-sm" title={e.name}>
                        {e.name}
                      </span>
                      <Prozentbalken wert={e.anzahl} max={stats.geraete[0]?.anzahl ?? 1} />
                      <span className="w-10 text-right text-sm tabular-nums font-medium">
                        {formatN(e.anzahl)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="rounded-xl border bg-card p-5 shadow-card">
              <h2 className="mb-4 text-sm font-semibold">HTTP-Statuscodes</h2>
              {stats.status_verteilung.length === 0 ? (
                <p className="text-sm text-muted-foreground">Keine Daten</p>
              ) : (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart
                    data={stats.status_verteilung.map((e) => ({ code: e.name, wert: e.anzahl }))}
                    margin={{ top: 8, right: 8, left: 0, bottom: 4 }}
                  >
                    <CartesianGrid
                      stroke="hsl(var(--border))"
                      strokeDasharray="3 3"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="code"
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: 'hsl(var(--border))' }}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                      width={32}
                    />
                    <Tooltip
                      contentStyle={{
                        background: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                      formatter={(v) => [formatN(Number(v)), 'Anfragen']}
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                    />
                    <Bar dataKey="wert" radius={[5, 5, 0, 0]} animationDuration={400}>
                      {stats.status_verteilung.map((e) => (
                        <Cell key={e.name} fill={statusFarbe(e.name)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="rounded-xl border bg-card p-5 shadow-card">
              <h2 className="mb-4 text-sm font-semibold">Top-Referrer</h2>
              {stats.top_referrer.length === 0 ? (
                <p className="text-sm text-muted-foreground">Keine Daten</p>
              ) : (
                <div className="space-y-2.5">
                  {stats.top_referrer.map((e) => (
                    <div key={e.name} className="flex items-center justify-between gap-3">
                      <span className="w-32 truncate text-sm" title={e.name}>
                        {e.name}
                      </span>
                      <Prozentbalken wert={e.anzahl} max={stats.top_referrer[0]?.anzahl ?? 1} />
                      <span className="w-10 text-right text-sm tabular-nums font-medium">
                        {formatN(e.anzahl)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-xl border bg-card p-5 shadow-card">
              <h2 className="mb-4 text-sm font-semibold">Top-ISPs</h2>
              {stats.top_isps.length === 0 ? (
                <p className="text-sm text-muted-foreground">Keine Daten</p>
              ) : (
                <div className="space-y-2.5">
                  {stats.top_isps.map((e) => (
                    <div key={e.name} className="flex items-center justify-between gap-3">
                      <span className="w-32 truncate text-sm" title={e.name}>
                        {e.name}
                      </span>
                      <Prozentbalken wert={e.anzahl} max={stats.top_isps[0]?.anzahl ?? 1} />
                      <span className="w-10 text-right text-sm tabular-nums font-medium">
                        {formatN(e.anzahl)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section>
            <div className="rounded-xl border bg-card shadow-card">
              <div className="border-b px-5 py-4">
                <h2 className="text-sm font-semibold">Letzte Besuche</h2>
                <p className="text-xs text-muted-foreground">
                  Die {stats.letzte_besuche.length} aktuellsten Aufrufe
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b bg-muted/30 text-left text-muted-foreground">
                      <th className="px-4 py-3 font-medium">Zeitpunkt</th>
                      <th className="px-4 py-3 font-medium">IP</th>
                      <th className="px-4 py-3 font-medium">Standort</th>
                      <th className="px-4 py-3 font-medium">Seite</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                      <th className="px-4 py-3 font-medium">Geraet</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.letzte_besuche.map((b, i) => {
                      const geoTeile = b.geo.split('|').map((s) => s.trim());
                      const land = geoTeile[0] ?? '';
                      const stadt = geoTeile[1] ?? '';
                      const isp = geoTeile[2] ?? '';
                      const status = parseInt(b.status, 10);
                      const statusKlasse =
                        status >= 500
                          ? 'text-red-500'
                          : status >= 400
                          ? 'text-yellow-500'
                          : status >= 300
                          ? 'text-blue-500'
                          : 'text-green-500';
                      return (
                        <tr
                          key={i}
                          className="border-b last:border-0 transition-colors hover:bg-muted/20"
                        >
                          <td className="whitespace-nowrap px-4 py-2.5 tabular-nums text-muted-foreground">
                            {b.zeitpunkt}
                          </td>
                          <td className="whitespace-nowrap px-4 py-2.5 font-mono">{b.ip}</td>
                          <td className="px-4 py-2.5">
                            <span className="font-medium">{land}</span>
                            {stadt && <span className="text-muted-foreground"> / {stadt}</span>}
                            {isp && (
                              <span
                                className="block max-w-[140px] truncate text-muted-foreground/70"
                                title={isp}
                              >
                                {isp}
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-2.5">
                            <span
                              className="max-w-[200px] truncate block font-mono"
                              title={b.pfad}
                            >
                              {b.pfad}
                            </span>
                          </td>
                          <td className={`whitespace-nowrap px-4 py-2.5 font-medium ${statusKlasse}`}>
                            {b.status}
                          </td>
                          <td className="max-w-[160px] truncate px-4 py-2.5 text-muted-foreground">
                            {b.ua.length > 50 ? b.ua.slice(0, 50) + '...' : b.ua}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
