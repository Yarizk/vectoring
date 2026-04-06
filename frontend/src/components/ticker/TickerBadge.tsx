import { cn } from '@/lib/utils';

interface TickerBadgeProps {
  symbol: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'highlight';
  onClick?: () => void;
  className?: string;
}

export function TickerBadge({
  symbol,
  size = 'md',
  variant = 'default',
  onClick,
  className,
}: TickerBadgeProps) {
  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  const variants = {
    default: 'bg-[var(--bg-elevated)] text-[var(--accent)] border-[var(--border)]',
    highlight: 'bg-[var(--accent)]/10 text-[var(--accent)] border-[var(--accent)]/30',
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center font-semibold rounded border transition-colors',
        sizes[size],
        variants[variant],
        onClick && 'hover:bg-[var(--bg-surface-hover)] cursor-pointer',
        className
      )}
    >
      {symbol}
    </button>
  );
}

interface TickerPillProps {
  symbol: string;
  name?: string;
  onClick?: () => void;
  className?: string;
}

export function TickerPill({ symbol, name, onClick, className }: TickerPillProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-2 px-3 py-1.5 rounded-full',
        'bg-[var(--bg-elevated)] border border-[var(--border)]',
        'hover:border-[var(--accent)] transition-colors',
        className
      )}
    >
      <span className="font-semibold text-[var(--accent)]">{symbol}</span>
      {name && (
        <span className="text-xs text-[var(--text-secondary)] truncate max-w-[120px]">
          {name}
        </span>
      )}
    </button>
  );
}
