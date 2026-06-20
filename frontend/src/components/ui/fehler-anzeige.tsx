import { cn } from '@/lib/utils';

interface Props {
  meldung: string;
  className?: string;
}

export function FehlerAnzeige({ meldung, className }: Props) {
  return (
    <div
      role="alert"
      className={cn(
        'rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive',
        className
      )}
    >
      {meldung}
    </div>
  );
}
