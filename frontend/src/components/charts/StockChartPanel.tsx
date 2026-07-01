import { useState, useEffect, useCallback } from 'react';
import { TrendingUp, BarChart2, Users, Loader, BarChart3, X } from 'lucide-react';
import { CandlestickChart } from './CandlestickChart';
import { FundamentalsCard } from './FundamentalsCard';
import { AnalystCard } from './AnalystCard';
import { getOhlcvChart, getFundamentals, type OhlcvBar } from '@/lib/api';
import { cn } from '@/lib/utils';

type Tab = 'chart' | 'fundamentals' | 'analyst';

const DAY_OPTIONS = [
  { value: 30, label: '1M' },
  { value: 90, label: '3M' },
  { value: 180, label: '6M' },
  { value: 365, label: '1Y' },
];

interface StockChartPanelProps {
  ticker: string;
  onClose?: () => void;
  className?: string;
}

export function StockChartPanel({ ticker, onClose, className = '' }: StockChartPanelProps) {
  const [tab, setTab] = useState<Tab>('chart');
  const [days, setDays] = useState(90);
  const [ohlcv, setOhlcv] = useState<OhlcvBar[] | null>(null);
  const [fundamentals, setFundamentals] = useState<Record<string, any> | null>(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [loadingFund, setLoadingFund] = useState(false);
  const [chartError, setChartError] = useState<string | null>(null);

  const fetchChart = useCallback(async (d: number) => {
    setLoadingChart(true);
    setChartError(null);
    try {
      const res = await getOhlcvChart(ticker, d);
      setOhlcv(res.data ?? []);
    } catch {
      setChartError('Chart data unavailable');
      setOhlcv([]);
    } finally {
      setLoadingChart(false);
    }
  }, [ticker]);

  const fetchFundamentals = useCallback(async () => {
    setLoadingFund(true);
    try {
      const res = await getFundamentals(ticker);
      setFundamentals(res.data ?? {});
    } catch {
      setFundamentals({});
    } finally {
      setLoadingFund(false);
    }
  }, [ticker]);

  useEffect(() => {
    setOhlcv(null);
    setFundamentals(null);
    setChartError(null);
    setDays(90);
    fetchChart(90);
    fetchFundamentals();
  }, [ticker, fetchChart, fetchFundamentals]);

  const handleDaysChange = (d: number) => {
    setDays(d);
    fetchChart(d);
  };

  const lastPrice = ohlcv && ohlcv.length > 0 ? ohlcv[ohlcv.length - 1] : null;
  const prevPrice = ohlcv && ohlcv.length > 1 ? ohlcv[ohlcv.length - 2] : null;
  const change = lastPrice && prevPrice
    ? ((lastPrice.close - prevPrice.close) / prevPrice.close) * 100
    : null;

  const tabs = [
    { id: 'chart' as Tab, label: 'Candlestick', icon: TrendingUp },
    { id: 'fundamentals' as Tab, label: 'Fundamental', icon: BarChart2 },
    { id: 'analyst' as Tab, label: 'Analis', icon: Users },
  ];

  return (
    <div className={`flex flex-col h-full bg-[var(--bg-surface)] ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <BarChart3 size={14} className="text-[var(--accent)]" />
          <span className="text-sm font-semibold text-[var(--text-primary)]">{ticker}</span>
          {lastPrice && (
            <span className="text-xs text-[var(--text-secondary)]">
              Rp {lastPrice.close.toLocaleString('id-ID')}
            </span>
          )}
          {change !== null && (
            <span className={cn(
              'text-xs font-medium',
              change >= 0 ? 'text-green-400' : 'text-red-400'
            )}>
              {change >= 0 ? '+' : ''}{change.toFixed(2)}%
            </span>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] transition-colors"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Tab bar */}
      <div className="flex items-center border-b border-[var(--border)] bg-[var(--bg-surface)] px-1">
        <div className="flex gap-0.5 flex-1 pt-1">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t-md transition-colors',
                tab === t.id
                  ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)] border border-[var(--border)] border-b-[var(--bg-elevated)]'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
              )}
            >
              <t.icon size={11} />
              {t.label}
            </button>
          ))}
        </div>

        {/* Day selector for chart tab */}
        {tab === 'chart' && (
          <div className="flex items-center gap-0.5 pr-1">
            {DAY_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => handleDaysChange(opt.value)}
                className={cn(
                  'px-2 py-0.5 text-xs rounded transition-colors',
                  days === opt.value
                    ? 'text-[var(--accent)] bg-[var(--bg-elevated)]'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {tab === 'chart' && (
          <div className="p-2">
            {loadingChart ? (
              <Loading label="Memuat chart..." />
            ) : chartError ? (
              <Empty label={chartError} />
            ) : ohlcv && ohlcv.length > 0 ? (
              <CandlestickChart ticker={ticker} data={ohlcv} />
            ) : (
              <Empty label="Data chart tidak tersedia" />
            )}
          </div>
        )}

        {tab === 'fundamentals' && (
          <div className="p-2">
            {loadingFund ? (
              <Loading label="Memuat fundamental..." />
            ) : fundamentals && Object.keys(fundamentals).length > 0 ? (
              <FundamentalsCard ticker={ticker} data={fundamentals} />
            ) : (
              <Empty label="Data fundamental tidak tersedia" />
            )}
          </div>
        )}

        {tab === 'analyst' && (
          <div className="p-2">
            {loadingFund ? (
              <Loading label="Memuat data analis..." />
            ) : fundamentals ? (
              <AnalystCard
                ticker={ticker}
                data={{
                  analyst_consensus: fundamentals.analyst_consensus,
                  analyst_ratings: fundamentals.analyst_ratings,
                }}
                currentPrice={lastPrice?.close}
              />
            ) : (
              <Empty label="Data analis tidak tersedia" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Loading({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <Loader size={18} className="text-[var(--accent)] animate-spin" />
      <span className="text-xs text-[var(--text-muted)]">{label}</span>
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-2">
      <BarChart2 size={20} className="text-[var(--text-muted)] opacity-30" />
      <span className="text-xs text-[var(--text-muted)]">{label}</span>
    </div>
  );
}
