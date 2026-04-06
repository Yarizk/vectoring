import { cn, formatRelativeTime, formatNumber } from '@/lib/utils';
import type { IngestionRun } from '@/types';

interface IngestionHistoryProps {
  history: IngestionRun[];
  className?: string;
}

export function IngestionHistory({ history, className }: IngestionHistoryProps) {
  return (
    <div className={cn('overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--bg-surface)]', className)}>
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--border)] bg-[var(--bg-elevated)]">
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Timestamp
            </th>
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Source
            </th>
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Documents
            </th>
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Chunks
            </th>
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--border)]">
          {history.map((run) => (
            <tr key={run.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
              <td className="px-6 py-4 text-[var(--text-secondary)]">
                {formatRelativeTime(run.timestamp)}
              </td>
              <td className="px-6 py-4 font-medium text-[var(--text-primary)]">
                {run.source}
              </td>
              <td className="px-6 py-4 text-[var(--text-secondary)]">
                {formatNumber(run.documentsProcessed)}
              </td>
              <td className="px-6 py-4 text-[var(--text-secondary)]">
                {formatNumber(run.chunksCreated)}
              </td>
              <td className="px-6 py-4">
                <StatusBadge status={run.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusBadge({ status }: { status: IngestionRun['status'] }) {
  const styles = {
    success: 'text-[var(--accent-green)]',
    partial: 'text-[var(--accent-gold)]',
    error: 'text-[var(--accent-red)]',
  };

  const labels = {
    success: '✅ Success',
    partial: '⚠️ Partial',
    error: '❌ Failed',
  };

  return (
    <span className={cn('text-sm font-medium', styles[status])}>
      {labels[status]}
    </span>
  );
}
