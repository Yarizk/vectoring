import { X, FileText, Database, TrendingUp } from 'lucide-react';
import { useChatStore, useUIStore } from '@/stores';
import { cn, formatPercentage, formatNumber } from '@/lib/utils';
import type { Source } from '@/types';

export function RightPanel() {
  const { selectedSources, selectedTicker } = useChatStore();
  const { rightPanelOpen, setRightPanelOpen } = useUIStore();

  if (!rightPanelOpen) return null;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
        <h3 className="font-medium text-sm">
          {selectedTicker ? selectedTicker.symbol : 'Sources'}
        </h3>
        <button
          onClick={() => setRightPanelOpen(false)}
          className="p-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)]
                     hover:bg-[var(--bg-surface-hover)] transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {selectedTicker ? (
          <TickerDetailView ticker={selectedTicker} />
        ) : selectedSources.length > 0 ? (
          <SourcesList sources={selectedSources} />
        ) : (
          <div className="p-6 text-center text-[var(--text-muted)] text-sm">
            <Database size={32} className="mx-auto mb-3 opacity-50" />
            <p>Select a source or ticker to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}

function SourcesList({ sources }: { sources: Source[] }) {
  return (
    <div className="p-4 space-y-3">
      <div className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
        Sources ({sources.length})
      </div>
      
      {sources.map((source, idx) => (
        <SourceCard key={source.id} source={source} index={idx + 1} />
      ))}
    </div>
  );
}

function SourceCard({ source, index }: { source: Source; index: number }) {
  const getIcon = () => {
    switch (source.source) {
      case 'ksei_pdf':
        return <FileText size={16} className="text-[var(--accent-gold)]" />;
      case 'ksei_json':
        return <Database size={16} className="text-[var(--accent-green)]" />;
      default:
        return <Database size={16} className="text-[var(--text-muted)]" />;
    }
  };

  const getTitle = () => {
    if (source.source === 'ksei_pdf') {
      return `${source.filename}, Page ${source.page_number}`;
    }
    if (source.source === 'ksei_json') {
      return `${source.ticker} - ${source.chunk_type}`;
    }
    return 'Unknown Source';
  };

  return (
    <div className="p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border)]
                    hover:border-[var(--border-hover)] transition-colors">
      <div className="flex items-start gap-3">
        <div className="mt-0.5">{getIcon()}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-[var(--text-muted)]">Source {index}</span>
            <span className="text-xs text-[var(--accent)]">
              {Math.round((1 - source.distance) * 100)}% match
            </span>
          </div>
          <div className="text-sm font-medium text-[var(--text-primary)] mt-1">
            {getTitle()}
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-2 line-clamp-3">
            {source.text_preview}
          </p>
          
          {source.date && (
            <div className="text-xs text-[var(--text-muted)] mt-2">
              Date: {source.date}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TickerDetailView({ ticker }: { ticker: any }) {
  return (
    <div className="p-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-baseline gap-2">
          <h2 className="text-2xl font-bold">{ticker.symbol}</h2>
          <span className="text-sm text-[var(--text-secondary)]">{ticker.name}</span>
        </div>
        <div className="flex items-center gap-2 mt-1 text-xs text-[var(--text-muted)]">
          <span>{ticker.sector}</span>
          {ticker.index?.map((idx: string) => (
            <span key={idx} className="px-1.5 py-0.5 rounded bg-[var(--bg-elevated)]">
              {idx}
            </span>
          ))}
        </div>
      </div>

      {/* Price (Placeholder for Stockbit) */}
      <div className="p-4 rounded-lg bg-[var(--bg-elevated)] mb-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">4,520</div>
            <div className="flex items-center gap-1 text-sm text-[var(--accent-green)]">
              <TrendingUp size={14} />
              +1.2%
            </div>
          </div>
          <div className="text-right text-xs text-[var(--text-muted)]">
            <div>PE: 12.4x</div>
            <div>PBV: 2.1x</div>
          </div>
        </div>
        <div className="text-xs text-[var(--text-muted)] mt-2">
          *Market data placeholder - Stockbit integration coming soon
        </div>
      </div>

      {/* Ownership */}
      <div className="mb-4">
        <div className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-3">
          Ownership Structure
        </div>
        
        {ticker.ownership?.map((item: any) => (
          <div key={item.category} className="mb-3">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-[var(--text-secondary)]">{item.category}</span>
              <span className="text-[var(--text-primary)]">{formatPercentage(item.percentage)}</span>
            </div>
            <div className="h-2 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--accent)] rounded-full transition-all"
                style={{ width: `${item.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Top Holders */}
      <div>
        <div className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-3">
          Top Holders
        </div>
        <div className="space-y-2">
          {ticker.topHolders?.slice(0, 5).map((holder: any, idx: number) => (
            <div key={idx} className="flex items-center justify-between py-2 border-b border-[var(--border)] last:border-0">
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
        <div className="mt-4 pt-4 border-t border-[var(--border)]">
          <div className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">
            Month-over-Month Change
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-[var(--bg-elevated)]">
              <div className="text-xs text-[var(--text-muted)]">Foreign</div>
              <div className={cn(
                'text-sm font-medium',
                ticker.momChanges.foreign >= 0 ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'
              )}>
                {ticker.momChanges.foreign >= 0 ? '▲' : '▼'} {formatPercentage(Math.abs(ticker.momChanges.foreign))}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--bg-elevated)]">
              <div className="text-xs text-[var(--text-muted)]">Domestic</div>
              <div className={cn(
                'text-sm font-medium',
                ticker.momChanges.domestic >= 0 ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'
              )}>
                {ticker.momChanges.domestic >= 0 ? '▲' : '▼'} {formatPercentage(Math.abs(ticker.momChanges.domestic))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
