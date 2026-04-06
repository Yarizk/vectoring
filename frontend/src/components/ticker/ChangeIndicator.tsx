import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn, formatPercentage } from '@/lib/utils';

interface ChangeIndicatorProps {
  value: number;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ChangeIndicator({
  value,
  showIcon = true,
  size = 'md',
  className,
}: ChangeIndicatorProps) {
  const isPositive = value > 0;
  const isNeutral = value === 0;

  const sizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const Icon = isPositive ? TrendingUp : isNeutral ? Minus : TrendingDown;
  const colorClass = isPositive
    ? 'text-[var(--accent-green)]'
    : isNeutral
    ? 'text-[var(--text-muted)]'
    : 'text-[var(--accent-red)]';

  return (
    <span className={cn('inline-flex items-center gap-1 font-medium', colorClass, sizes[size], className)}>
      {showIcon && <Icon size={size === 'lg' ? 18 : size === 'md' ? 16 : 14} />}
      <span>{isPositive ? '+' : ''}{formatPercentage(value)}</span>
    </span>
  );
}

interface PriceChangeProps {
  price: number;
  change: number;
  changePercent: number;
  className?: string;
}

export function PriceChange({ price, change, changePercent, className }: PriceChangeProps) {
  const isPositive = change >= 0;

  return (
    <div className={cn('flex flex-col', className)}>
      <span className="text-2xl font-bold text-[var(--text-primary)]">
        {price.toLocaleString()}
      </span>
      <div className="flex items-center gap-2">
        <span
          className={cn(
            'text-sm font-medium',
            isPositive ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'
          )}
        >
          {isPositive ? '+' : ''}{change.toLocaleString()}
        </span>
        <span
          className={cn(
            'text-xs px-1.5 py-0.5 rounded',
            isPositive
              ? 'bg-green-500/10 text-green-400'
              : 'bg-red-500/10 text-red-400'
          )}
        >
          {isPositive ? '+' : ''}{formatPercentage(changePercent)}
        </span>
      </div>
    </div>
  );
}
