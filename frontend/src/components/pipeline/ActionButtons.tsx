import { RefreshCw, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

interface ActionButtonsProps {
  isIngesting: boolean;
  onIngest: () => void;
  onClearAndIngest?: () => void;
  className?: string;
}

export function ActionButtons({
  isIngesting,
  onIngest,
  onClearAndIngest,
  className,
}: ActionButtonsProps) {
  return (
    <div className={cn('flex items-center gap-4', className)}>
      <Button
        onClick={onIngest}
        disabled={isIngesting}
        isLoading={isIngesting}
        className="gap-2"
      >
        <RefreshCw size={18} className={cn(isIngesting && 'animate-spin')} />
        {isIngesting ? 'Processing...' : 'Re-ingest Data'}
      </Button>

      {onClearAndIngest && (
        <Button
          variant="secondary"
          onClick={onClearAndIngest}
          disabled={isIngesting}
          className="gap-2"
        >
          <Trash2 size={18} />
          Clear & Re-ingest
        </Button>
      )}
    </div>
  );
}
