import { useChatStore } from '@/stores';
import { UserMessage } from './UserMessage';
import { AIMessage } from './AIMessage';
import { QuickActionsGrid } from './QuickActions';
import { KseiLogo } from '@/components/ui/KseiLogo';

export function ChatContainer() {
  const { messages, isLoading } = useChatStore();

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full px-8">
        <div className="mb-4">
          <KseiLogo size={40} />
        </div>
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
          KSEI Intelligence
        </h2>
        <p className="text-xs text-[var(--text-secondary)] text-center max-w-sm mb-6">
          Query Indonesian stock ownership data from KSEI.
          Foreign ownership, top holders, and market trends.
        </p>

        <QuickActionsGrid className="w-full max-w-md" />
      </div>
    );
  }

  return (
    <div className="flex flex-col py-2">
      {messages.map((message) => (
        message.role === 'user' ? (
          <UserMessage key={message.id} message={message} />
        ) : (
          <AIMessage key={message.id} message={message} />
        )
      ))}

      {isLoading && (
        <div className="px-4 py-3">
          <div className="flex items-center gap-2 text-[var(--text-muted)]">
            <div className="flex gap-0.5">
              <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-xs">Analyzing KSEI data...</span>
          </div>
        </div>
      )}
    </div>
  );
}
