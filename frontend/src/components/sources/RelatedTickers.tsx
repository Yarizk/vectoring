import { TrendingUp } from 'lucide-react';
import { TickerBadge } from '@/components/ticker/TickerBadge';
import { ChangeIndicator } from '@/components/ticker/ChangeIndicator';
import { cn } from '@/lib/utils';

interface RelatedTicker {
  symbol: string;
  name: string;
  change: number;
}

interface RelatedTickersProps {
  tickers: RelatedTicker[];
  onTickerClick?: (symbol: string) => void;
  className?: string;
}

export function RelatedTickers({ tickers, onTickerClick, className }: RelatedTickersProps) {
  if (!tickers.length) return null;

  return (
    <div className={cn('space-y-3', className)}>
      <div className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
        Related Tickers
      </div>
      <div className="flex flex-wrap gap-2">
        {tickers.map((ticker) => (
          <button
            key={ticker.symbol}
            onClick={() => onTickerClick?.(ticker.symbol)}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg',
              'bg-[var(--bg-elevated)] border border-[var(--border)]',
              'hover:border-[var(--accent)] transition-colors'
            )}
          >
            <TickerBadge symbol={ticker.symbol} size="sm" />
            <ChangeIndicator value={ticker.change} showIcon={false} size="sm" />
          </button>
        ))}
      </div>
    </div>
  );
}

interface SectorTickersProps {
  sector: string;
  tickers: string[];
  onTickerClick?: (symbol: string) => void;
  className?: string;
}

export function SectorTickers({ sector, tickers, onTickerClick, className }: SectorTickersProps) {
  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center gap-2">
        <TrendingUp size={14} className="text-[var(--text-muted)]" />
        <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
          {sector}
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {tickers.map((symbol) => (
          <TickerBadge
            key={symbol}
            symbol={symbol}
            size="sm"
            onClick={() => onTickerClick?.(symbol)}
          />
        ))}
      </div>
    </div>
  );
}
