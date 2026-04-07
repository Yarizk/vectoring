import { useState, useRef, useCallback } from 'react';
import { Send } from 'lucide-react';
import { useChatStore } from '@/stores';
import { useChat } from '@/hooks/useChat';
import { ModeSelector, QualityBadge } from './ModeSelector';
import type { Message } from '@/types';

export function ChatInput() {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { mode, setMode, isLoading, messages } = useChatStore();
  const { sendMessage } = useChat();

  // Get quality from last AI message
  const lastQuality = messages
    .slice()
    .reverse()
    .find((m): m is Message & { quality: NonNullable<Message['quality']> } =>
      m.role === 'assistant' && !!m.quality
    )?.quality;

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;
    const text = input.trim();
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    await sendMessage(text);
  };

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const handleInput = useCallback((e: React.FormEvent<HTMLTextAreaElement>) => {
    const target = e.currentTarget;
    target.style.height = 'auto';
    target.style.height = Math.min(target.scrollHeight, 180) + 'px';
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask a question... (Enter to send)"
          className="w-full bg-[var(--bg-elevated)] text-sm text-[var(--text-primary)] rounded-lg
                     border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none
                     pl-3 pr-10 py-2.5 min-h-[44px] max-h-[180px] resize-none
                     placeholder-[var(--text-muted)] transition-colors"
          rows={1}
          disabled={isLoading}
        />

        <button
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading}
          className="absolute right-2 bottom-2 p-1.5 rounded
                     bg-[var(--accent)] text-white
                     hover:bg-[var(--accent-hover)] disabled:opacity-40
                     disabled:cursor-not-allowed transition-colors"
        >
          <Send size={14} />
        </button>
      </div>

      <div className="mt-1.5 flex items-center justify-between">
        <ModeSelector value={mode} onChange={setMode} />
        <div className="flex items-center gap-2">
          <QualityBadge quality={lastQuality} />
          <span className="text-xs text-[var(--text-muted)]">
            <kbd className="px-1 py-0.5 rounded bg-[var(--bg-elevated)] text-xs">Enter</kbd> send
          </span>
        </div>
      </div>
    </div>
  );
}
