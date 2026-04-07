import { TrendingDown, Building2, Users, PieChart } from 'lucide-react';
import { useUIStore } from '@/stores';
import { useChat } from '@/hooks/useChat';
import { QUICK_ACTIONS } from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

const iconMap: Record<string, LucideIcon> = {
  TrendingDown,
  Building2,
  Users,
  PieChart,
};

interface QuickActionsProps {
  variant?: 'sidebar' | 'inline';
  className?: string;
}

export function QuickActions({ variant = 'sidebar', className }: QuickActionsProps) {
  const { sendMessage } = useChat();
  const { setActivePage } = useUIStore();

  const handleAction = (prompt: string) => {
    setActivePage('chat');
    sendMessage(prompt);
  };

  if (variant === 'inline') {
    return (
      <div className={cn('flex flex-wrap gap-1.5', className)}>
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.id}
            onClick={() => handleAction(action.prompt)}
            className={cn(
              'px-2.5 py-1 rounded text-xs',
              'bg-[var(--bg-elevated)] text-[var(--text-secondary)]',
              'border border-[var(--border)]',
              'hover:border-[var(--accent)] hover:text-[var(--text-primary)]',
              'transition-colors'
            )}
          >
            {action.label}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className={cn('space-y-0.5', className)}>
      {QUICK_ACTIONS.map((action) => {
        const Icon = iconMap[action.icon] || PieChart;
        return (
          <button
            key={action.id}
            onClick={() => handleAction(action.prompt)}
            className={cn(
              'w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-xs',
              'text-[var(--text-secondary)]',
              'hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]',
              'transition-colors'
            )}
          >
            <Icon size={13} className="text-[var(--text-muted)]" />
            <span>{action.label}</span>
          </button>
        );
      })}
    </div>
  );
}

export function QuickActionsGrid({ className }: { className?: string }) {
  const { sendMessage } = useChat();
  const { setActivePage } = useUIStore();

  const handleAction = (prompt: string) => {
    setActivePage('chat');
    sendMessage(prompt);
  };

  return (
    <div className={cn('grid grid-cols-2 gap-2', className)}>
      {QUICK_ACTIONS.map((action) => {
        const Icon = iconMap[action.icon] || PieChart;
        return (
          <button
            key={action.id}
            onClick={() => handleAction(action.prompt)}
            className={cn(
              'flex flex-col items-start gap-1.5 p-2.5 rounded-lg',
              'bg-[var(--bg-elevated)] border border-[var(--border)]',
              'hover:border-[var(--accent)] hover:bg-[var(--bg-surface-hover)]',
              'transition-all group'
            )}
          >
            <Icon size={15} className="text-[var(--accent)]" />
            <span className="text-xs font-medium text-[var(--text-primary)] group-hover:text-[var(--accent)]">
              {action.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
