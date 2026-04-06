import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CollapsibleProps {
  title: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
  className?: string;
}

export function Collapsible({
  title,
  children,
  defaultOpen = true,
  className,
}: CollapsibleProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={cn('border border-[var(--border)] rounded-lg bg-[var(--bg-surface)]', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-[var(--bg-surface-hover)] transition-colors"
      >
        <span className="font-medium text-[var(--text-primary)]">{title}</span>
        {isOpen ? (
          <ChevronUp size={18} className="text-[var(--text-muted)]" />
        ) : (
          <ChevronDown size={18} className="text-[var(--text-muted)]" />
        )}
      </button>
      {isOpen && <div className="px-4 py-3 border-t border-[var(--border)]">{children}</div>}
    </div>
  );
}
