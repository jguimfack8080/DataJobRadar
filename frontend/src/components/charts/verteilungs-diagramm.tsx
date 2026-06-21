'use client';

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { formatGehalt } from '@/lib/utils';

interface Datenpunkt {
  gruppe: string;
  gehalt_median: number | null;
  gehalt_p25: number | null;
  gehalt_p75: number | null;
}

interface Props {
  daten: Datenpunkt[];
  hoehe?: number;
  onGruppeKlick?: (gruppe: string) => void;
}

export function VerteilungsDiagramm({ daten, hoehe = 360, onGruppeKlick }: Props) {
  const aufbereitet = daten.map((eintrag) => ({
    gruppe: eintrag.gruppe,
    median: eintrag.gehalt_median ?? 0,
    spannweite: Math.max(0, (eintrag.gehalt_p75 ?? 0) - (eintrag.gehalt_p25 ?? 0)),
    p25: eintrag.gehalt_p25 ?? 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={hoehe}>
      <BarChart
        data={aufbereitet}
        layout="vertical"
        margin={{ top: 12, right: 16, left: 32, bottom: 8 }}
      >
        <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
          tickFormatter={(wert) => formatGehalt(wert)}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="gruppe"
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={140}
        />
        <Tooltip
          contentStyle={{
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: 8,
            fontSize: 12,
          }}
          formatter={(wert, name) => {
            if (name === 'p25') return [formatGehalt(Number(wert)), 'P25'];
            if (name === 'spannweite') return [formatGehalt(Number(wert)), 'Spannweite (P25-P75)'];
            return [formatGehalt(Number(wert)), 'Median'];
          }}
        />
        <Bar dataKey="p25" stackId="a" fill="transparent" />
        <Bar
          dataKey="spannweite"
          stackId="a"
          fill="hsl(var(--accent))"
          radius={[0, 6, 6, 0]}
          cursor={onGruppeKlick ? 'pointer' : 'default'}
          onClick={(payload) => {
            const gruppe = (payload as { gruppe?: string })?.gruppe;
            if (gruppe && onGruppeKlick) onGruppeKlick(gruppe);
          }}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
