import { FileText, Database, TrendingUp } from 'lucide-react';
import { cn, formatNumber, formatRelativeTime } from '@/lib/utils';
import type { DataSource } from '@/types';

interface DataSourceTableProps {
  sources: DataSource[];
  className?: string;
}

export function DataSourceTable({ sources, className }: DataSourceTableProps) {
  return (
    <div className={cn('overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--bg-surface)]', className)}>
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--border)] bg-[var(--bg-elevated)]">
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Source
            </th>
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Documents
            </th>
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Chunks
            </th>
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Last Update
            </th>
            <th className="px-6 py-4 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              Fresh
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--border)]">
          {sources.map((source) => (
            <tr key={source.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
              <td className="px-6 py-4">
                <div className="flex items-center gap-3">
                  <SourceIcon type={source.type} />
                  <span className="font-medium text-[var(--text-primary)]">{source.name}</span>
                </div>
              </td>
              <td className="px-6 py-4">
                <StatusBadge status={source.status} />
              </td>
              <td className="px-6 py-4 text-[var(--text-secondary)]">
                {formatNumber(source.documentCount)}
              </td>
              <td className="px-6 py-4 text-[var(--text-secondary)]">
                {formatNumber(source.chunkCount)}
              </td>
              <td className="px-6 py-4 text-[var(--text-secondary)]">
                {formatRelativeTime(source.lastUpdate)}
              </td>
              <td className="px-6 py-4">
                {source.isFresh ? (
                  <span className="text-[var(--accent-green)]">✓</span>
                ) : (
                  <span className="text-[var(--accent-gold)]">⚠</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SourceIcon({ type }: { type: DataSource['type'] }) {
  const icons = {
    ksei_pdf: <FileText size={18} className="text-[var(--accent-gold)]" />,
    ksei_json: <Database size={18} className="text-[var(--accent-green)]" />,
    market_data: <TrendingUp size={18} className="text-[var(--accent)]" />,
  };
  return icons[type] || icons.ksei_json;
}

function StatusBadge({ status }: { status: DataSource['status'] }) {
  const styles = {
    ok: 'bg-green-500/10 text-green-400 border-green-500/20',
    warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    error: 'bg-red-500/10 text-red-400 border-red-500/20',
  };

  const labels = {
    ok: '🟢 OK',
    warning: '🟡 WARN',
    error: '🔴 ERROR',
  };

  return (
    <span className={cn('px-2 py-1 rounded text-xs font-medium border', styles[status])}>
      {labels[status]}
    </span>
  );
}
