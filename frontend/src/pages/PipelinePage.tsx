import { usePipeline } from '@/hooks';
import { HealthCards } from '@/components/pipeline/HealthCards';
import { DataSourceTable } from '@/components/pipeline/DataSourceTable';
import { IngestionHistory } from '@/components/pipeline/IngestionHistory';
import { ActionButtons } from '@/components/pipeline/ActionButtons';
import { RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

export function PipelinePage() {
  const {
    stats,
    dataSources,
    ingestionHistory,
    isLoading,
    isIngesting,
    error,
    refresh,
    ingest,
  } = usePipeline();

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Pipeline Monitor</h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Data ingestion status and system health
          </p>
        </div>
        <button
          onClick={refresh}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg
                     bg-[var(--bg-elevated)] text-[var(--text-secondary)]
                     hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]
                     disabled:opacity-50 transition-colors"
        >
          <RefreshCw size={16} className={cn(isLoading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* Health Cards */}
      <HealthCards stats={stats} className="mb-8" />

      {/* Data Sources */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Data Sources</h2>
        <DataSourceTable sources={dataSources} />
      </div>

      {/* Ingestion History */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Ingestion History</h2>
        <IngestionHistory history={ingestionHistory} />
      </div>

      {/* Actions */}
      <ActionButtons
        isIngesting={isIngesting}
        onIngest={() => ingest(false)}
        onClearAndIngest={() => ingest(true)}
      />

      {error && (
        <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
          {error}
        </div>
      )}
    </div>
  );
}
