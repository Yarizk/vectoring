import { Activity, Database, Layers } from 'lucide-react';
import { cn, formatNumber } from '@/lib/utils';
import type { PipelineStats } from '@/types';

interface HealthCardsProps {
  stats: PipelineStats | null;
  className?: string;
}

export function HealthCards({ stats, className }: HealthCardsProps) {
  const isHealthy = stats?.jatevoStatus || stats?.ollamaStatus;
  const provider = stats?.llmProvider || 'unknown';

  const cards = [
    {
      icon: Activity,
      label: 'System Health',
      value: isHealthy ? 'Operational' : 'Degraded',
      status: isHealthy ? 'ok' as const : 'warning' as const,
      detail: provider === 'jatevo' ? 'Jatevo API' : 'Ollama Local',
    },
    {
      icon: Database,
      label: 'Total Documents',
      value: formatNumber(stats?.documentCount || 0),
      status: 'ok' as const,
      detail: `${stats?.embeddingModel || 'Unknown'} embeddings`,
    },
    {
      icon: Layers,
      label: 'Total Chunks',
      value: formatNumber(stats?.documentCount || 0),
      status: 'ok' as const,
      detail: 'Ready for search',
    },
  ];

  return (
    <div className={cn('grid grid-cols-1 md:grid-cols-3 gap-4', className)}>
      {cards.map((card) => (
        <HealthCard key={card.label} {...card} />
      ))}
    </div>
  );
}

interface HealthCardProps {
  icon: React.ElementType;
  label: string;
  value: string;
  status: 'ok' | 'warning' | 'error';
  detail: string;
}

function HealthCard({ icon: Icon, label, value, status, detail }: HealthCardProps) {
  const statusColors = {
    ok: 'text-[var(--accent-green)]',
    warning: 'text-[var(--accent-gold)]',
    error: 'text-[var(--accent-red)]',
  };

  return (
    <div className="p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border)]">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-[var(--text-muted)] mb-1">{label}</div>
          <div className="text-2xl font-bold text-[var(--text-primary)]">{value}</div>
          <div className="text-xs text-[var(--text-secondary)] mt-1">{detail}</div>
        </div>
        <div className={cn('p-2 rounded-lg bg-[var(--bg-elevated)]', statusColors[status])}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}
