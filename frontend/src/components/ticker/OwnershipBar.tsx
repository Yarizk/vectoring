import { cn, formatPercentage } from '@/lib/utils';

interface OwnershipBarProps {
  label: string;
  percentage: number;
  color?: 'blue' | 'green' | 'gold' | 'purple';
  showPercentage?: boolean;
  className?: string;
}

export function OwnershipBar({
  label,
  percentage,
  color = 'blue',
  showPercentage = true,
  className,
}: OwnershipBarProps) {
  const colors = {
    blue: 'bg-[var(--accent)]',
    green: 'bg-[var(--accent-green)]',
    gold: 'bg-[var(--accent-gold)]',
    purple: 'bg-[var(--accent-purple)]',
  };

  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-[var(--text-secondary)]">{label}</span>
        {showPercentage && (
          <span className="font-medium text-[var(--text-primary)]">
            {formatPercentage(percentage)}
          </span>
        )}
      </div>
      <div className="h-2 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-500', colors[color])}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}

interface OwnershipStackProps {
  items: Array<{
    label: string;
    percentage: number;
    color?: OwnershipBarProps['color'];
  }>;
  className?: string;
}

export function OwnershipStack({ items, className }: OwnershipStackProps) {
  return (
    <div className={cn('space-y-3', className)}>
      {items.map((item, index) => (
        <OwnershipBar
          key={item.label}
          label={item.label}
          percentage={item.percentage}
          color={item.color || 'blue'}
        />
      ))}
    </div>
  );
}
