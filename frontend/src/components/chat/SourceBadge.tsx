import { FileText, Database, TrendingUp, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Source } from '@/types';

interface SourceBadgeProps {
  count: number;
  latency?: number;
  onClick?: () => void;
  className?: string;
}

export function SourceBadge({ count, latency, onClick, className }: SourceBadgeProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs',
        'bg-[var(--bg-elevated)] text-[var(--text-secondary)]',
        'hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)]',
        'border border-[var(--border)] hover:border-[var(--border-hover)]',
        'transition-colors',
        className
      )}
    >
      <FileText size={14} />
      <span>{count} sources</span>
      {latency && (
        <>
          <span className="text-[var(--border-hover)]">|</span>
          <Clock size={12} />
          <span>{latency.toFixed(1)}s</span>
        </>
      )}
    </button>
  );
}

interface SourceTypeBadgeProps {
  type: Source['source'];
  className?: string;
}

export function SourceTypeBadge({ type, className }: SourceTypeBadgeProps) {
  const config = {
    ksei_pdf: {
      icon: FileText,
      label: 'PDF',
      color: 'text-[var(--accent-gold)] bg-[var(--accent-gold)]/10 border-[var(--accent-gold)]/20',
    },
    ksei_json: {
      icon: Database,
      label: 'JSON',
      color: 'text-[var(--accent-green)] bg-[var(--accent-green)]/10 border-[var(--accent-green)]/20',
    },
    market_data: {
      icon: TrendingUp,
      label: 'Market',
      color: 'text-[var(--accent)] bg-[var(--accent)]/10 border-[var(--accent)]/20',
    },
  };

  const { icon: Icon, label, color } = config[type] || config.ksei_json;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border',
        color,
        className
      )}
    >
      <Icon size={12} />
      {label}
    </span>
  );
}

interface RelevanceBadgeProps {
  distance: number;
  className?: string;
}

export function RelevanceBadge({ distance, className }: RelevanceBadgeProps) {
  // Convert distance to relevance percentage (lower distance = higher relevance)
  const relevance = Math.round((1 - Math.min(distance, 1)) * 100);
  
  let color = 'text-[var(--accent-red)]';
  if (relevance >= 80) color = 'text-[var(--accent-green)]';
  else if (relevance >= 60) color = 'text-[var(--accent-gold)]';
  else if (relevance >= 40) color = 'text-[var(--accent)]';

  return (
    <span className={cn('text-xs font-medium', color, className)}>
      {relevance}% match
    </span>
  );
}
