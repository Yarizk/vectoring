import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine,
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
} from 'recharts';

interface Ratios {
  date: string;
  pe_ttm: number | null;
  pe_forward: number | null;
  pb: number | null;
  ev_ebitda: number | null;
  roe: number | null;
  roa: number | null;
  roic: number | null;
  gross_margin: number | null;
  operating_margin: number | null;
  debt_equity: number | null;
  current_ratio: number | null;
  interest_coverage: number | null;
  dividend_yield: number | null;
  payout_ratio: number | null;
  earnings_yield: number | null;
}

interface FinancialsMap {
  [metric: string]: {
    [year: string]: {
      [period: string]: number;
    };
  };
}

interface FundamentalsData {
  ratios?: Ratios;
  financials?: FinancialsMap;
}

interface FundamentalsCardProps {
  ticker: string;
  data: FundamentalsData;
  className?: string;
}

function pct(v: number | null | undefined) {
  if (v == null) return 'N/A';
  return `${v.toFixed(1)}%`;
}

function x(v: number | null | undefined) {
  if (v == null) return 'N/A';
  return `${v.toFixed(1)}x`;
}

function ScoreBar({ label, value, min, max, invert = false, format }: {
  label: string; value: number | null | undefined;
  min: number; max: number; invert?: boolean;
  format: (v: number) => string;
}) {
  if (value == null) return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 text-[var(--text-muted)] shrink-0">{label}</span>
      <span className="text-[var(--text-muted)]">N/A</span>
    </div>
  );
  const pctPos = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  const score = invert ? 100 - pctPos : pctPos;
  const color = score >= 66 ? '#22c55e' : score >= 33 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 text-[var(--text-muted)] shrink-0">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-[var(--border)] overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="w-16 text-right text-[var(--text-primary)] font-mono">{format(value)}</span>
    </div>
  );
}

export function FundamentalsCard({ ticker, data, className = '' }: FundamentalsCardProps) {
  const r = data.ratios;
  const fin = data.financials;

  // Build quarterly chart data for Revenue & Net Income
  const revenueData: { period: string; value: number }[] = [];
  const netIncomeData: { period: string; value: number }[] = [];

  if (fin) {
    const periods = ['Q1', 'Q2', 'Q3', 'Q4'];
    const revMetric = fin['Revenue'] || {};
    const niMetric = fin['Net Income'] || {};

    const years = [...new Set([...Object.keys(revMetric), ...Object.keys(niMetric)])].sort().slice(-2);
    for (const yr of years) {
      for (const p of periods) {
        const revVal = revMetric[yr]?.[p];
        const niVal = niMetric[yr]?.[p];
        const label = `${yr} ${p}`;
        if (revVal != null) revenueData.push({ period: label, value: revVal });
        if (niVal != null) netIncomeData.push({ period: label, value: niVal });
      }
    }
  }

  const radarData = r ? [
    { subject: 'ROE', A: Math.min(100, (r.roe || 0) / 30 * 100) },
    { subject: 'ROA', A: Math.min(100, (r.roa || 0) / 10 * 100) },
    { subject: 'Margin', A: Math.min(100, (r.gross_margin || 0) / 50 * 100) },
    { subject: 'Likuiditas', A: Math.min(100, ((r.current_ratio || 0) / 3) * 100) },
    { subject: 'Div Yield', A: Math.min(100, (r.dividend_yield || 0) / 8 * 100) },
    { subject: 'Earnings', A: Math.min(100, (r.earnings_yield || 0) / 15 * 100) },
  ] : [];

  return (
    <div className={`rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] overflow-hidden ${className}`}>
      <div className="px-3 py-2 border-b border-[var(--border)]">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">{ticker} — Fundamental</h3>
        {r && <p className="text-xs text-[var(--text-muted)]">Per {r.date}</p>}
      </div>

      <div className="p-3 grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: ratio bars */}
        {r && (
          <div className="space-y-4">
            <div>
              <p className="text-xs font-medium text-[var(--text-secondary)] mb-2 uppercase tracking-wide">Valuasi</p>
              <div className="space-y-1.5">
                <ScoreBar label="PE TTM" value={r.pe_ttm} min={0} max={50} invert format={x} />
                <ScoreBar label="PE Forward" value={r.pe_forward} min={0} max={50} invert format={x} />
                <ScoreBar label="PB" value={r.pb} min={0} max={8} invert format={x} />
                <ScoreBar label="EV/EBITDA" value={r.ev_ebitda} min={0} max={30} invert format={x} />
                <ScoreBar label="Div Yield" value={r.dividend_yield} min={0} max={10} format={v => pct(v)} />
              </div>
            </div>
            <div>
              <p className="text-xs font-medium text-[var(--text-secondary)] mb-2 uppercase tracking-wide">Profitabilitas</p>
              <div className="space-y-1.5">
                <ScoreBar label="ROE" value={r.roe} min={0} max={30} format={v => pct(v)} />
                <ScoreBar label="ROA" value={r.roa} min={0} max={10} format={v => pct(v)} />
                <ScoreBar label="ROIC" value={r.roic} min={0} max={30} format={v => pct(v)} />
                <ScoreBar label="Gross Margin" value={r.gross_margin} min={0} max={80} format={v => pct(v)} />
                <ScoreBar label="Op Margin" value={r.operating_margin} min={0} max={50} format={v => pct(v)} />
              </div>
            </div>
            <div>
              <p className="text-xs font-medium text-[var(--text-secondary)] mb-2 uppercase tracking-wide">Kesehatan</p>
              <div className="space-y-1.5">
                <ScoreBar label="Debt/Equity" value={r.debt_equity} min={0} max={3} invert format={x} />
                <ScoreBar label="Current Ratio" value={r.current_ratio} min={0} max={3} format={x} />
                <ScoreBar label="Int. Coverage" value={r.interest_coverage} min={0} max={10} format={x} />
              </div>
            </div>
          </div>
        )}

        {/* Right: radar + revenue/NI chart */}
        <div className="space-y-4">
          {radarData.length > 0 && (
            <div>
              <p className="text-xs font-medium text-[var(--text-secondary)] mb-1 uppercase tracking-wide">Profil Kualitas</p>
              <ResponsiveContainer width="100%" height={160}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.08)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <Radar dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}

          {revenueData.length > 0 && (
            <div>
              <p className="text-xs font-medium text-[var(--text-secondary)] mb-1 uppercase tracking-wide">Revenue Kuartal</p>
              <ResponsiveContainer width="100%" height={100}>
                <BarChart data={revenueData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                  <XAxis dataKey="period" tick={{ fill: '#64748b', fontSize: 9 }} tickLine={false} axisLine={false} />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 4, fontSize: 11 }}
                    formatter={(v) => {
                      const n = Number(v);
                      return [n >= 1e12 ? `${(n/1e12).toFixed(1)}T` : n >= 1e9 ? `${(n/1e9).toFixed(1)}B` : `${(n/1e6).toFixed(0)}M`, 'Revenue'];
                    }}
                  />
                  <Bar dataKey="value" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {netIncomeData.length > 0 && (
            <div>
              <p className="text-xs font-medium text-[var(--text-secondary)] mb-1 uppercase tracking-wide">Net Income Kuartal</p>
              <ResponsiveContainer width="100%" height={100}>
                <BarChart data={netIncomeData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                  <XAxis dataKey="period" tick={{ fill: '#64748b', fontSize: 9 }} tickLine={false} axisLine={false} />
                  <YAxis hide />
                  <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 4, fontSize: 11 }}
                    formatter={(v) => {
                      const n = Number(v);
                      return [n >= 1e12 ? `${(n/1e12).toFixed(1)}T` : n >= 1e9 ? `${(n/1e9).toFixed(1)}B` : `${(n/1e6).toFixed(0)}M`, 'Net Income'];
                    }}
                  />
                  <Bar dataKey="value" fill="#22c55e" radius={[2, 2, 0, 0]}
                    label={false}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
