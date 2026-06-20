'use client';

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { formatDatum, formatZahl } from '@/lib/utils';

interface Datenpunkt {
  tag: string;
  anzahl: number;
}

interface Props {
  daten: Datenpunkt[];
  hoehe?: number;
}

export function LinienDiagramm({ daten, hoehe = 320 }: Props) {
  return (
    <ResponsiveContainer width="100%" height={hoehe}>
      <AreaChart data={daten} margin={{ top: 12, right: 8, left: 0, bottom: 8 }}>
        <defs>
          <linearGradient id="djr-akzent" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity={0.4} />
            <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="tag"
          tickFormatter={(wert) => formatDatum(wert)}
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: 'hsl(var(--border))' }}
        />
        <YAxis
          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          width={40}
          tickFormatter={(wert) => formatZahl(wert)}
        />
        <Tooltip
          cursor={{ stroke: 'hsl(var(--border))' }}
          contentStyle={{
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: 8,
            fontSize: 12,
          }}
          formatter={(wert) => [formatZahl(Number(wert)), 'Anzeigen']}
          labelFormatter={(wert) => formatDatum(String(wert))}
          labelStyle={{ color: 'hsl(var(--foreground))' }}
        />
        <Area
          type="monotone"
          dataKey="anzahl"
          stroke="hsl(var(--accent))"
          strokeWidth={2}
          fill="url(#djr-akzent)"
          isAnimationActive
          animationDuration={500}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
