import { User } from 'lucide-react';
import type { Message } from '@/types';
import { formatDate } from '@/lib/utils';

interface UserMessageProps {
  message: Message;
}

export function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="px-4 py-3 border-b border-[var(--border)]">
      <div className="flex gap-3 max-w-4xl mx-auto">
        <div className="flex-shrink-0 w-6 h-6 rounded bg-[var(--bg-elevated)]
                        flex items-center justify-center">
          <User size={13} className="text-[var(--text-secondary)]" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-xs font-medium text-[var(--text-primary)]">You</span>
            <span className="text-xs text-[var(--text-muted)]">
              {formatDate(message.timestamp)}
            </span>
          </div>
          <div className="text-sm text-[var(--text-primary)] leading-relaxed">
            {message.content}
          </div>
        </div>
      </div>
    </div>
  );
}
