import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface AnalystConsensus {
  date: string;
  rating: string | null;
  target_median: number | null;
  target_high: number | null;
  target_low: number | null;
  rev_up: number | null;
  rev_dn: number | null;
}

interface AnalystRating {
  date: string;
  broker: string;
  rating: string;
  target: number | null;
  analyst: string | null;
}

interface AnalystData {
  analyst_consensus?: AnalystConsensus;
  analyst_ratings?: AnalystRating[];
}

interface AnalystCardProps {
  ticker: string;
  data: AnalystData;
  currentPrice?: number;
  className?: string;
}

const RATING_COLOR: Record<string, string> = {
  BUY: '#22c55e',
  STRONG_BUY: '#16a34a',
  OUTPERFORM: '#4ade80',
  HOLD: '#f59e0b',
  NEUTRAL: '#fbbf24',
  UNDERPERFORM: '#f87171',
  SELL: '#ef4444',
  STRONG_SELL: '#dc2626',
};

function ratingColor(rating: string | null | undefined) {
  if (!rating) return '#94a3b8';
  return RATING_COLOR[rating.toUpperCase().replace(/ /g, '_')] || '#94a3b8';
}

function isBullish(rating: string | null | undefined) {
  if (!rating) return null;
  const r = rating.toUpperCase();
  if (r.includes('BUY') || r.includes('OUTPERFORM') || r.includes('OVERWEIGHT')) return true;
  if (r.includes('SELL') || r.includes('UNDERPERFORM') || r.includes('UNDERWEIGHT')) return false;
  return null;
}

function formatPrice(v: number | null | undefined) {
  if (v == null) return 'N/A';
  return `Rp ${v.toLocaleString('id-ID')}`;
}

function formatUpside(target: number | null | undefined, current: number | undefined) {
  if (!target || !current) return null;
  const pct = ((target - current) / current) * 100;
  return pct;
}

export function AnalystCard({ ticker, data, currentPrice, className = '' }: AnalystCardProps) {
  const c = data.analyst_consensus;
  const ratings = data.analyst_ratings || [];

  // Build pie data from individual ratings
  const ratingCounts: Record<string, number> = {};
  for (const r of ratings) {
    const key = r.rating?.toUpperCase() || 'UNKNOWN';
    ratingCounts[key] = (ratingCounts[key] || 0) + 1;
  }

  const pieData = Object.entries(ratingCounts).map(([name, value]) => ({
    name, value, fill: ratingColor(name),
  }));

  const upside = formatUpside(c?.target_median, currentPrice);
  const consensusBull = isBullish(c?.rating);

  return (
    <div className={`rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] overflow-hidden ${className}`}>
      <div className="px-3 py-2 border-b border-[var(--border)]">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">{ticker} — Analis</h3>
        {c && <p className="text-xs text-[var(--text-muted)]">Per {c.date}</p>}
      </div>

      <div className="p-3 grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Consensus panel */}
        {c && (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div
                className="px-3 py-1.5 rounded-lg text-sm font-bold"
                style={{ background: `${ratingColor(c.rating)}20`, color: ratingColor(c.rating) }}
              >
                {c.rating || 'N/A'}
              </div>
              {consensusBull !== null && (
                consensusBull
                  ? <TrendingUp size={16} className="text-green-400" />
                  : <TrendingDown size={16} className="text-red-400" />
              )}
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">Target Median</span>
                <span className="text-[var(--text-primary)] font-medium">{formatPrice(c.target_median)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">Target Tinggi</span>
                <span className="text-green-400">{formatPrice(c.target_high)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">Target Rendah</span>
                <span className="text-red-400">{formatPrice(c.target_low)}</span>
              </div>
              {upside !== null && (
                <div className="flex justify-between text-xs">
                  <span className="text-[var(--text-muted)]">Upside (vs harga)</span>
                  <span className={upside >= 0 ? 'text-green-400' : 'text-red-400'}>
                    {upside >= 0 ? '+' : ''}{upside.toFixed(1)}%
                  </span>
                </div>
              )}
            </div>

            {(c.rev_up != null || c.rev_dn != null) && (
              <div className="flex gap-3 text-xs">
                <span className="text-green-400">↑ {c.rev_up ?? 0} revisi naik</span>
                <span className="text-red-400">↓ {c.rev_dn ?? 0} revisi turun</span>
                <span className="text-[var(--text-muted)]">(30 hari)</span>
              </div>
            )}
          </div>
        )}

        {/* Pie chart of individual ratings */}
        {pieData.length > 0 && (
          <div>
            <p className="text-xs font-medium text-[var(--text-secondary)] mb-1 uppercase tracking-wide">
              Distribusi Rating ({ratings.length} broker)
            </p>
            <div className="flex items-center gap-3">
              <ResponsiveContainer width={100} height={100}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={28} outerRadius={44}
                    dataKey="value" paddingAngle={2}>
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', fontSize: 11 }}
                    formatter={(v, name) => [v, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1">
                {pieData.map(d => (
                  <div key={d.name} className="flex items-center gap-1.5 text-xs">
                    <span className="w-2 h-2 rounded-sm" style={{ background: d.fill }} />
                    <span className="text-[var(--text-muted)]">{d.name}</span>
                    <span className="text-[var(--text-primary)] font-medium">{d.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Individual broker ratings table */}
      {ratings.length > 0 && (
        <div className="border-t border-[var(--border)]">
          <div className="px-3 py-1.5">
            <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide">Rating Individual</p>
          </div>
          <div className="max-h-40 overflow-y-auto">
            <table className="w-full text-xs">
              <tbody>
                {ratings.slice(0, 12).map((r, i) => (
                  <tr key={i} className="border-t border-[var(--border)] hover:bg-[var(--bg-surface-hover)]">
                    <td className="px-3 py-1.5 text-[var(--text-secondary)]">{r.broker}</td>
                    <td className="px-3 py-1.5">
                      <span className="px-1.5 py-0.5 rounded text-xs font-medium"
                        style={{ background: `${ratingColor(r.rating)}20`, color: ratingColor(r.rating) }}>
                        {r.rating}
                      </span>
                    </td>
                    <td className="px-3 py-1.5 text-right text-[var(--text-primary)]">{formatPrice(r.target)}</td>
                    <td className="px-3 py-1.5 text-right text-[var(--text-muted)]">{r.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
