import { TrendingUp, TrendingDown, DollarSign, Calendar, BarChart3 } from 'lucide-react';
import type { TickerEnrichment } from '@/types';

interface MarketContextProps {
  enrichment: Record<string, TickerEnrichment>;
}

function formatIDR(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1e12) return `Rp ${(value / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `Rp ${(value / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `Rp ${(value / 1e6).toFixed(0)}M`;
  return `Rp ${value.toLocaleString()}`;
}

function PerfBadge({ label, value }: { label: string; value: number | null }) {
  if (value === null || value === undefined) return null;
  const isPositive = value > 0;
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs px-1.5 py-0.5 rounded
      ${isPositive ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
      {label}: {isPositive ? '+' : ''}{value}%
    </span>
  );
}

function TickerCard({ ticker, data }: { ticker: string; data: TickerEnrichment }) {
  const flow = data.foreign_flow;
  const perf = data.price_performance;
  const actions = data.corp_actions;

  const hasData = flow || perf || (actions && actions.length > 0);
  if (!hasData) return null;

  return (
    <div className="p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border)]">
      <div className="flex items-center gap-2 mb-2">
        <BarChart3 size={14} className="text-[var(--accent)]" />
        <span className="text-sm font-semibold text-[var(--text-primary)]">{ticker}</span>
        <span className="text-xs text-[var(--text-muted)]">Live Data</span>
      </div>

      {/* Foreign Flow */}
      {flow && (
        <div className="flex items-center gap-2 mb-2">
          {flow.foreign_net > 0 ? (
            <TrendingUp size={14} className="text-green-400" />
          ) : (
            <TrendingDown size={14} className="text-red-400" />
          )}
          <span className="text-sm text-[var(--text-secondary)]">
            Foreign {flow.foreign_net > 0 ? 'Net Buy' : 'Net Sell'}:{' '}
            <span className={flow.foreign_net > 0 ? 'text-green-400' : 'text-red-400'}>
              {formatIDR(Math.abs(flow.foreign_net))}
            </span>
          </span>
        </div>
      )}

      {/* Price Performance */}
      {perf && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          <PerfBadge label="1W" value={perf.performance_1w} />
          <PerfBadge label="1M" value={perf.performance_1m} />
          <PerfBadge label="3M" value={perf.performance_3m} />
          <PerfBadge label="YTD" value={perf.performance_ytd} />
          <PerfBadge label="1Y" value={perf.performance_1y} />
        </div>
      )}

      {/* Corporate Actions */}
      {actions && actions.length > 0 && (
        <div className="mt-2 pt-2 border-t border-[var(--border)]">
          {actions.map((action, i) => (
            <div key={i} className="flex items-start gap-1.5 text-xs text-[var(--text-muted)]">
              <Calendar size={12} className="mt-0.5 text-[var(--accent-gold)]" />
              <span>
                {action.description}
                {action.ex_date && (
                  <span className="text-[var(--text-muted)]"> (ex: {action.ex_date})</span>
                )}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function MarketContext({ enrichment }: MarketContextProps) {
  const tickers = Object.keys(enrichment);
  if (tickers.length === 0) return null;

  // Check if any ticker has actual data
  const hasAnyData = tickers.some((t) => {
    const d = enrichment[t];
    return d.foreign_flow || d.price_performance || (d.corp_actions && d.corp_actions.length > 0);
  });

  if (!hasAnyData) return null;

  return (
    <div className="mt-4 space-y-2">
      <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
        <DollarSign size={12} />
        <span>Market Context</span>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {tickers.map((ticker) => (
          <TickerCard key={ticker} ticker={ticker} data={enrichment[ticker]} />
        ))}
      </div>
    </div>
  );
}
