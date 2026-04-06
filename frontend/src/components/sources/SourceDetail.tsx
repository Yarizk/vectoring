import { FileText, Database, ExternalLink } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { RelevanceBadge } from '@/components/chat/SourceBadge';
import { cn } from '@/lib/utils';
import type { Source } from '@/types';

interface SourceDetailProps {
  source: Source;
  className?: string;
}

export function SourceDetail({ source, className }: SourceDetailProps) {
  const getIcon = () => {
    switch (source.source) {
      case 'ksei_pdf':
        return <FileText size={20} className="text-[var(--accent-gold)]" />;
      case 'ksei_json':
        return <Database size={20} className="text-[var(--accent-green)]" />;
      default:
        return <Database size={20} className="text-[var(--text-muted)]" />;
    }
  };

  const getSourceType = () => {
    switch (source.source) {
      case 'ksei_pdf':
        return 'KSEI PDF';
      case 'ksei_json':
        return 'KSEI JSON';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-[var(--bg-elevated)]">{getIcon()}</div>
        <div className="flex-1">
          <div className="text-sm text-[var(--text-muted)]">{getSourceType()}</div>
          <div className="font-medium text-[var(--text-primary)]">
            {source.source === 'ksei_pdf'
              ? source.filename
              : source.ticker}
          </div>
          {source.source === 'ksei_pdf' && (
            <div className="text-sm text-[var(--text-secondary)]">
              Page {source.page_number}
            </div>
          )}
        </div>
      </div>

      {/* Relevance */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-[var(--text-muted)]">Relevance</span>
        <RelevanceBadge distance={source.distance} />
      </div>

      {/* Content Preview */}
      <Card className="p-4 bg-[var(--bg-elevated)]">
        <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
          {source.text_preview}
        </p>
      </Card>

      {/* Metadata */}
      <div className="space-y-2">
        <div className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
          Metadata
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-[var(--text-muted)]">Source</div>
          <div className="text-[var(--text-primary)]">{getSourceType()}</div>
          
          {source.date && (
            <>
              <div className="text-[var(--text-muted)]">Date</div>
              <div className="text-[var(--text-primary)]">{source.date}</div>
            </>
          )}
          
          {source.ticker && (
            <>
              <div className="text-[var(--text-muted)]">Ticker</div>
              <div className="text-[var(--accent)]">{source.ticker}</div>
            </>
          )}
          
          {source.chunk_type && (
            <>
              <div className="text-[var(--text-muted)]">Type</div>
              <div className="text-[var(--text-primary)]">{source.chunk_type}</div>
            </>
          )}
        </div>
      </div>

      {/* View Full Document Button */}
      {source.source === 'ksei_pdf' && (
        <button
          className={cn(
            'w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg',
            'bg-[var(--bg-elevated)] text-[var(--text-secondary)]',
            'hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]',
            'transition-colors'
          )}
        >
          <ExternalLink size={16} />
          View Full Document
        </button>
      )}
    </div>
  );
}
