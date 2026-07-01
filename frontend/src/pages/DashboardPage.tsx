import { useState, useEffect } from 'react';
import {
  BarChart3, Database, Zap, Search, TrendingUp, RefreshCw, AlertCircle,
} from 'lucide-react';
import { getStats, checkHealth } from '@/lib/api';
import { StockChartPanel } from '@/components/charts';

const FEATURED_TICKERS = [
  'BBRI', 'BBCA', 'BMRI', 'TLKM', 'ASII',
  'GOTO', 'BSDE', 'UNVR', 'ICBP', 'PGAS',
];

export function DashboardPage() {
  const [searchInput, setSearchInput] = useState('');
  const [activeTicker, setActiveTicker] = useState('BBRI');
  const [stats, setStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [loadingStats, setLoadingStats] = useState(true);

  useEffect(() => {
    Promise.all([getStats(), checkHealth()])
      .then(([s, h]) => { setStats(s); setHealth(h); })
      .catch(() => {})
      .finally(() => setLoadingStats(false));
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const sym = searchInput.trim().toUpperCase();
    if (sym.length >= 2) {
      setActiveTicker(sym);
      setSearchInput('');
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center gap-4 px-4 py-2.5 border-b border-[var(--border)] bg-[var(--bg-surface)]">
        <h1 className="text-sm font-semibold text-[var(--text-primary)]">Market Explorer</h1>

        {/* Ticker search */}
        <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 max-w-xs">
          <div className="relative flex-1">
            <Search size={13} className="absolute left-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              value={searchInput}
              onChange={e => setSearchInput(e.target.value.toUpperCase())}
              placeholder="Cari ticker… (mis. BBRI)"
              className="w-full pl-7 pr-3 py-1 text-xs rounded border border-[var(--border)]
                         bg-[var(--bg-elevated)] text-[var(--text-primary)] placeholder-[var(--text-muted)]
                         focus:outline-none focus:border-[var(--accent)] transition-colors"
              maxLength={6}
            />
          </div>
          <button
            type="submit"
            className="px-2.5 py-1 text-xs rounded bg-[var(--accent)] text-white
                       hover:bg-[var(--accent-hover)] transition-colors"
          >
            Go
          </button>
        </form>

        {/* Quick ticker chips */}
        <div className="flex gap-1 flex-wrap">
          {FEATURED_TICKERS.map(t => (
            <button
              key={t}
              onClick={() => setActiveTicker(t)}
              className={[
                'px-1.5 py-0.5 rounded text-xs font-mono font-medium transition-colors border',
                activeTicker === t
                  ? 'bg-[var(--accent)] text-white border-[var(--accent)]'
                  : 'bg-[var(--bg-elevated)] text-[var(--text-muted)] border-[var(--border)] hover:text-[var(--accent)] hover:border-[var(--accent)]',
              ].join(' ')}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Main content: chart + stats */}
      <div className="flex flex-1 overflow-hidden gap-0">
        {/* Chart panel — takes most space */}
        <div className="flex-1 overflow-hidden border-r border-[var(--border)]">
          <StockChartPanel ticker={activeTicker} />
        </div>

        {/* Stats sidebar */}
        <div className="w-[220px] flex-shrink-0 overflow-y-auto p-3 space-y-3">
          <SystemStats stats={stats} health={health} loading={loadingStats} />
        </div>
      </div>
    </div>
  );
}

function SystemStats({ stats, health, loading }: { stats: any; health: any; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
        <RefreshCw size={12} className="animate-spin" />
        Loading…
      </div>
    );
  }

  const providerOk = health?.provider_connected;
  const provider = health?.provider ?? stats?.llm_provider ?? '—';

  return (
    <>
      {/* Provider status */}
      <div className="rounded border border-[var(--border)] bg-[var(--bg-elevated)] p-2.5">
        <div className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide mb-2">
          Provider
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full ${providerOk ? 'bg-green-400' : 'bg-red-400'}`} />
          <span className="text-xs text-[var(--text-primary)] font-mono uppercase">{provider}</span>
        </div>
        {health?.config_errors?.length > 0 && (
          <div className="mt-1.5 space-y-0.5">
            {health.config_errors.map((e: string, i: number) => (
              <div key={i} className="flex items-start gap-1 text-xs text-yellow-400">
                <AlertCircle size={10} className="mt-0.5 shrink-0" />
                <span>{e}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ChromaDB */}
      {stats && (
        <div className="rounded border border-[var(--border)] bg-[var(--bg-elevated)] p-2.5">
          <div className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide mb-2">
            Vector DB
          </div>
          <Stat icon={Database} label="Documents" value={stats.document_count?.toLocaleString() ?? '—'} />
          <Stat icon={Zap} label="Model" value={stats.embedding_model ?? '—'} />
          <Stat icon={BarChart3} label="Collection" value={stats.collection_name ?? '—'} />
        </div>
      )}

      {/* LLM model */}
      {stats?.jatevo_model && (
        <div className="rounded border border-[var(--border)] bg-[var(--bg-elevated)] p-2.5">
          <div className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide mb-2">
            LLM
          </div>
          <Stat icon={TrendingUp} label="Model" value={stats.jatevo_model} />
        </div>
      )}

      {/* Tip */}
      <div className="rounded border border-[var(--border)] bg-[var(--bg-elevated)] p-2.5 text-xs text-[var(--text-muted)] space-y-1">
        <p className="font-medium text-[var(--text-secondary)]">Tips</p>
        <p>Ketik ticker di kotak pencarian atau klik chip di atas untuk melihat chart.</p>
        <p>Tab <span className="text-[var(--accent)]">Fundamental</span> menampilkan PE, ROE, margin.</p>
        <p>Tab <span className="text-[var(--accent)]">Analis</span> menampilkan konsensus broker.</p>
      </div>
    </>
  );
}

function Stat({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-xs mb-1 last:mb-0">
      <div className="flex items-center gap-1.5 text-[var(--text-muted)]">
        <Icon size={11} />
        {label}
      </div>
      <span className="text-[var(--text-primary)] font-mono text-right truncate max-w-[100px]" title={value}>
        {value}
      </span>
    </div>
  );
}
