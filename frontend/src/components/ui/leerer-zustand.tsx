import { cn } from '@/lib/utils';

interface Props {
  titel: string;
  beschreibung?: string;
  className?: string;
}

export function LeererZustand({ titel, beschreibung, className }: Props) {
  return (
    <div className={cn('flex flex-col items-center justify-center rounded-lg border border-dashed p-10 text-center', className)}>
      <p className="text-sm font-medium">{titel}</p>
      {beschreibung && <p className="mt-1 text-sm text-muted-foreground">{beschreibung}</p>}
    </div>
  );
}
