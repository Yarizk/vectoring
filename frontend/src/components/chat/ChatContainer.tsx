import { useChatStore } from '@/stores';
import { UserMessage } from './UserMessage';
import { AIMessage } from './AIMessage';
import { QuickActionsGrid } from './QuickActions';
import { Database, MessageSquare } from 'lucide-react';

export function ChatContainer() {
  const { messages, isLoading } = useChatStore();

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full px-8">
        <div className="w-16 h-16 rounded-2xl bg-[var(--bg-elevated)] flex items-center justify-center mb-6">
          <Database size={32} className="text-[var(--accent)]" />
        </div>
        <h2 className="text-2xl font-semibold text-[var(--text-primary)] mb-2">
          KSEI Intelligence
        </h2>
        <p className="text-[var(--text-secondary)] text-center max-w-md mb-8">
          Ask questions about Indonesian stock ownership data from KSEI.
          Get insights on foreign ownership, top holders, and market trends.
        </p>
        
        <QuickActionsGrid className="w-full max-w-lg" />
      </div>
    );
  }

  return (
    <div className="flex flex-col py-4">
      {messages.map((message) => (
        message.role === 'user' ? (
          <UserMessage key={message.id} message={message} />
        ) : (
          <AIMessage key={message.id} message={message} />
        )
      ))}
      
      {isLoading && (
        <div className="px-4 py-6">
          <div className="flex items-center gap-2 text-[var(--text-muted)]">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm">Analyzing KSEI data...</span>
          </div>
        </div>
      )}
    </div>
  );
}
