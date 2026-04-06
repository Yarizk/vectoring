import { TrendingUp } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { TickerBadge } from './TickerBadge';
import { PriceChange, ChangeIndicator } from './ChangeIndicator';
import { OwnershipStack } from './OwnershipBar';
import { cn, formatPercentage } from '@/lib/utils';
import type { TickerDetail } from '@/types';

interface TickerQuickViewProps {
  ticker: TickerDetail;
  className?: string;
}

export function TickerQuickView({ ticker, className }: TickerQuickViewProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div>
        <div className="flex items-baseline gap-3 mb-1">
          <TickerBadge symbol={ticker.symbol} size="lg" />
          <span className="text-sm text-[var(--text-secondary)]">{ticker.name}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
          <span>{ticker.sector}</span>
          {ticker.index?.map((idx) => (
            <span
              key={idx}
              className="px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-secondary)]"
            >
              {idx}
            </span>
          ))}
        </div>
      </div>

      {/* Price Section (Placeholder) */}
      <Card className="p-4 bg-[var(--bg-elevated)]">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">
              {ticker.price?.toLocaleString() || '4,520'}
            </div>
            <div className="flex items-center gap-1 text-sm text-[var(--accent-green)]">
              <TrendingUp size={14} />
              +1.2%
            </div>
          </div>
          <div className="text-right text-xs text-[var(--text-muted)] space-y-1">
            <div>PE: {ticker.pe?.toFixed(1) || '12.4'}x</div>
            <div>PBV: {ticker.pbv?.toFixed(1) || '2.1'}x</div>
          </div>
        </div>
        <div className="text-xs text-[var(--text-muted)] mt-3 pt-3 border-t border-[var(--border)]">
          *Market data placeholder - Stockbit integration coming soon
        </div>
      </Card>

      {/* Ownership Structure */}
      <div>
        <h4 className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-3">
          Ownership Structure
        </h4>
        <OwnershipStack
          items={ticker.ownership?.map((o, i) => ({
            label: o.category,
            percentage: o.percentage,
            color: i === 0 ? 'blue' : i === 1 ? 'green' : 'gold',
          })) || [
            { label: 'Pemerintah RI', percentage: 53.2, color: 'blue' },
            { label: 'Foreign', percentage: 24.1, color: 'green' },
            { label: 'Domestic Public', percentage: 22.7, color: 'gold' },
          ]}
        />
      </div>

      {/* Top Holders */}
      <div>
        <h4 className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-3">
          Top Holders
        </h4>
        <div className="space-y-2">
          {(ticker.topHolders || []).slice(0, 5).map((holder, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between py-2 border-b border-[var(--border)] last:border-0"
            >
              <div>
                <div className="text-sm text-[var(--text-primary)]">{holder.name}</div>
                <div className="text-xs text-[var(--text-muted)]">{holder.type}</div>
              </div>
              <div className="text-sm font-medium text-[var(--text-primary)]">
                {formatPercentage(holder.percentage)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* MoM Changes */}
      {ticker.momChanges && (
        <div className="pt-4 border-t border-[var(--border)]">
          <h4 className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-3">
            Month-over-Month Change
          </h4>
          <div className="grid grid-cols-2 gap-3">
            <Card className="p-3">
              <div className="text-xs text-[var(--text-muted)]">Foreign</div>
              <ChangeIndicator value={ticker.momChanges.foreign} />
            </Card>
            <Card className="p-3">
              <div className="text-xs text-[var(--text-muted)]">Domestic</div>
              <ChangeIndicator value={ticker.momChanges.domestic} />
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
