import { User } from 'lucide-react';
import type { Message } from '@/types';
import { formatDate } from '@/lib/utils';

interface UserMessageProps {
  message: Message;
}

export function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="px-4 py-6 border-b border-[var(--border)]">
      <div className="flex gap-4 max-w-4xl mx-auto">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-[var(--bg-elevated)] 
                        flex items-center justify-center">
          <User size={16} className="text-[var(--text-secondary)]" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-[var(--text-primary)]">You</span>
            <span className="text-xs text-[var(--text-muted)]">
              {formatDate(message.timestamp)}
            </span>
          </div>
          <div className="text-[var(--text-primary)] leading-relaxed">
            {message.content}
          </div>
        </div>
      </div>
    </div>
  );
}
