import { useState } from 'react';
import { Search, Zap, Trash2 } from 'lucide-react';
import { useChatStore, useUIStore } from '@/stores';
import { QuickActions } from '@/components/chat/QuickActions';
import { formatRelativeTime } from '@/lib/utils';
import type { Message } from '@/types';

export function LeftSidebar() {
  const [searchQuery, setSearchQuery] = useState('');
  const { messages, clearChat } = useChatStore();
  const { setActivePage } = useUIStore();

  // Filter messages based on search
  const filteredMessages = searchQuery
    ? messages.filter((m) => 
        m.content.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : messages;

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-2 border-b border-[var(--border)]">
        <div className="relative">
          <Search
            size={12}
            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
          />
          <input
            type="text"
            placeholder="Search history..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[var(--bg-elevated)] text-xs rounded pl-7 pr-2.5 py-1.5
                       text-[var(--text-primary)] placeholder-[var(--text-muted)]
                       border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none
                       transition-colors"
          />
        </div>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto">
        {filteredMessages.length === 0 ? (
          <div className="p-3 text-center text-[var(--text-muted)] text-xs">
            {searchQuery ? 'No results found' : 'No chat history yet'}
          </div>
        ) : searchQuery ? (
          // Search results
          <div className="p-2 space-y-0.5">
            {filteredMessages
              .filter((m) => m.role === 'user')
              .map((msg) => (
                <button
                  key={msg.id}
                  onClick={() => setActivePage('chat')}
                  className="w-full px-2 py-1.5 text-left text-xs text-[var(--text-secondary)]
                             hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]
                             truncate transition-colors rounded"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[var(--accent)]">▸</span>
                    <span className="truncate">{msg.content}</span>
                  </div>
                </button>
              ))}
          </div>
        ) : (
          // Grouped by date
          Object.entries(
            filteredMessages.reduce((groups, msg) => {
              const date = new Date(msg.timestamp).toDateString();
              if (!groups[date]) groups[date] = [];
              groups[date].push(msg);
              return groups;
            }, {} as Record<string, Message[]>)
          ).map(([date, msgs]) => (
            <div key={date} className="mb-2">
              <div className="px-2 py-1 text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
                {formatRelativeTime(date)}
              </div>
              {msgs
                .filter((m) => m.role === 'user')
                .map((msg) => (
                  <button
                    key={msg.id}
                    onClick={() => setActivePage('chat')}
                    className="w-full px-2 py-1.5 text-left text-xs text-[var(--text-secondary)]
                               hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]
                               truncate transition-colors rounded"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-[var(--accent)]">▸</span>
                      <span className="truncate">{msg.content}</span>
                    </div>
                  </button>
                ))}
            </div>
          ))
        )}
      </div>

      {/* Quick Actions */}
      <div className="p-2 border-t border-[var(--border)]">
        <div className="flex items-center gap-1.5 mb-1 text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider px-0.5">
          <Zap size={11} />
          Quick Actions
        </div>
        <QuickActions variant="sidebar" />
      </div>

      {/* Clear Chat */}
      {messages.length > 0 && (
        <div className="p-2 border-t border-[var(--border)]">
          <button
            onClick={clearChat}
            className="w-full flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded
                       text-xs text-[var(--text-muted)] hover:text-[var(--accent-red)]
                       hover:bg-[var(--bg-surface-hover)] transition-colors"
          >
            <Trash2 size={12} />
            Clear History
          </button>
        </div>
      )}
    </div>
  );
}
