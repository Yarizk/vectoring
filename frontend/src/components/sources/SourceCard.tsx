import { FileText, Database } from 'lucide-react';
import { cn } from '@/lib/utils';
import { RelevanceBadge } from '@/components/chat/SourceBadge';
import type { Source } from '@/types';

interface SourceCardProps {
  source: Source;
  index?: number;
  onClick?: () => void;
  className?: string;
}

export function SourceCard({ source, index, onClick, className }: SourceCardProps) {
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
    <div
      onClick={onClick}
      className={cn(
        'p-4 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border)]',
        'hover:border-[var(--border-hover)] transition-colors',
        onClick && 'cursor-pointer',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5">{getIcon()}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-[var(--text-muted)]">
              {index ? `Source ${index}` : 'Source'}
            </span>
            <RelevanceBadge distance={source.distance} />
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
