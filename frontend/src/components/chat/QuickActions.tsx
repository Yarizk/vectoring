import { TrendingDown, Building2, Users, PieChart } from 'lucide-react';
import { useChatStore, useUIStore } from '@/stores';
import { QUICK_ACTIONS } from '@/lib/constants';
import { cn, generateId } from '@/lib/utils';
import type { Message } from '@/types';
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
  const { addMessage, setLoading } = useChatStore();
  const { setActivePage } = useUIStore();

  const handleAction = (prompt: string) => {
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: prompt,
      timestamp: new Date(),
    };
    addMessage(userMessage);
    setLoading(true);
    setActivePage('chat');
    
    // TODO: Call API
    setTimeout(() => setLoading(false), 1000);
  };

  if (variant === 'inline') {
    return (
      <div className={cn('flex flex-wrap gap-2', className)}>
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.id}
            onClick={() => handleAction(action.prompt)}
            className={cn(
              'px-3 py-2 rounded-lg text-sm',
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
    <div className={cn('space-y-1', className)}>
      {QUICK_ACTIONS.map((action) => {
        const Icon = iconMap[action.icon] || PieChart;
        return (
          <button
            key={action.id}
            onClick={() => handleAction(action.prompt)}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm',
              'text-[var(--text-secondary)]',
              'hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]',
              'transition-colors'
            )}
          >
            <Icon size={16} className="text-[var(--text-muted)]" />
            <span>{action.label}</span>
          </button>
        );
      })}
    </div>
  );
}

export function QuickActionsGrid({ className }: { className?: string }) {
  const { addMessage, setLoading } = useChatStore();
  const { setActivePage } = useUIStore();

  const handleAction = (prompt: string) => {
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: prompt,
      timestamp: new Date(),
    };
    addMessage(userMessage);
    setLoading(true);
    setActivePage('chat');
    setTimeout(() => setLoading(false), 1000);
  };

  return (
    <div className={cn('grid grid-cols-2 gap-3', className)}>
      {QUICK_ACTIONS.map((action) => {
        const Icon = iconMap[action.icon] || PieChart;
        return (
          <button
            key={action.id}
            onClick={() => handleAction(action.prompt)}
            className={cn(
              'flex flex-col items-start gap-2 p-4 rounded-xl',
              'bg-[var(--bg-elevated)] border border-[var(--border)]',
              'hover:border-[var(--accent)] hover:bg-[var(--bg-surface-hover)]',
              'transition-all group'
            )}
          >
            <Icon size={20} className="text-[var(--accent)]" />
            <span className="text-sm font-medium text-[var(--text-primary)] group-hover:text-[var(--accent)]">
              {action.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
