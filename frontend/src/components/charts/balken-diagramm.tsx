'use client';

import { useRouter } from 'next/navigation';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { formatZahl } from '@/lib/utils';

interface Datenpunkt {
  beschriftung: string;
  wert: number;
  ziel?: string;
}

interface Props {
  daten: Datenpunkt[];
  hoehe?: number;
  beschriftungYAchse?: string;
}

export function BalkenDiagramm({ daten, hoehe = 320, beschriftungYAchse }: Props) {
  const router = useRouter();
  const klick = (eintrag: Datenpunkt | undefined) => {
    if (eintrag?.ziel) router.push(eintrag.ziel);
  };
  return (
    <ResponsiveContainer width="100%" height={hoehe}>
      <BarChart data={daten} margin={{ top: 12, right: 8, left: 0, bottom: 8 }}>
        <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="beschriftung"
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
          label={
            beschriftungYAchse
              ? {
                  value: beschriftungYAchse,
                  angle: -90,
                  position: 'insideLeft',
                  fill: 'hsl(var(--muted-foreground))',
                }
              : undefined
          }
        />
        <Tooltip
          cursor={{ fill: 'hsl(var(--muted))' }}
          contentStyle={{
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: 8,
            fontSize: 12,
          }}
          formatter={(wert) => [formatZahl(Number(wert)), 'Anzahl']}
          labelStyle={{ color: 'hsl(var(--foreground))' }}
        />
        <Bar
          dataKey="wert"
          fill="hsl(var(--accent))"
          radius={[6, 6, 0, 0]}
          animationDuration={400}
          animationEasing="ease-out"
          cursor={daten.some((p) => p.ziel) ? 'pointer' : 'default'}
          onClick={(payload) => klick(payload as unknown as Datenpunkt)}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
