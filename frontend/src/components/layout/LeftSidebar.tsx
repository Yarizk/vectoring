import { useState } from 'react';
import { Search, Clock, Zap, Trash2 } from 'lucide-react';
import { useChatStore, useUIStore } from '@/stores';
import { QuickActions } from '@/components/chat/QuickActions';
import { cn, formatRelativeTime, generateId } from '@/lib/utils';
import type { Message } from '@/types';

export function LeftSidebar() {
  const [searchQuery, setSearchQuery] = useState('');
  const { messages, addMessage, setLoading, clearChat } = useChatStore();
  const { setActivePage } = useUIStore();

  // Group messages by date
  const groupedMessages = messages.reduce((groups, msg) => {
    const date = new Date(msg.timestamp).toDateString();
    if (!groups[date]) groups[date] = [];
    groups[date].push(msg);
    return groups;
  }, {} as Record<string, Message[]>);

  // Filter messages based on search
  const filteredMessages = searchQuery
    ? messages.filter((m) => 
        m.content.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : messages;

  const handleQuickAction = (prompt: string) => {
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

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-3 border-b border-[var(--border)]">
        <div className="relative">
          <Search 
            size={14} 
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" 
          />
          <input
            type="text"
            placeholder="Search history..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[var(--bg-elevated)] text-sm rounded-lg pl-9 pr-3 py-2 
                       text-[var(--text-primary)] placeholder-[var(--text-muted)]
                       border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none
                       transition-colors"
          />
        </div>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto">
        {filteredMessages.length === 0 ? (
          <div className="p-4 text-center text-[var(--text-muted)] text-sm">
            {searchQuery ? 'No results found' : 'No chat history yet'}
          </div>
        ) : searchQuery ? (
          // Search results
          <div className="p-3 space-y-1">
            {filteredMessages
              .filter((m) => m.role === 'user')
              .map((msg) => (
                <button
                  key={msg.id}
                  onClick={() => setActivePage('chat')}
                  className="w-full px-3 py-2 text-left text-sm text-[var(--text-secondary)] 
                             hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]
                             truncate transition-colors"
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
            <div key={date} className="mb-4">
              <div className="px-3 py-2 text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
                {formatRelativeTime(date)}
              </div>
              {msgs
                .filter((m) => m.role === 'user')
                .map((msg) => (
                  <button
                    key={msg.id}
                    onClick={() => setActivePage('chat')}
                    className="w-full px-3 py-2 text-left text-sm text-[var(--text-secondary)] 
                               hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]
                               truncate transition-colors"
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
      <div className="p-3 border-t border-[var(--border)]">
        <div className="flex items-center gap-2 mb-2 text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
          <Zap size={12} />
          Quick Actions
        </div>
        <QuickActions variant="sidebar" />
      </div>

      {/* Clear Chat */}
      {messages.length > 0 && (
        <div className="p-3 border-t border-[var(--border)]">
          <button
            onClick={clearChat}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg
                       text-sm text-[var(--text-muted)] hover:text-[var(--accent-red)]
                       hover:bg-[var(--bg-surface-hover)] transition-colors"
          >
            <Trash2 size={14} />
            Clear History
          </button>
        </div>
      )}
    </div>
  );
}
