import { useState, useRef, useCallback } from 'react';
import { Send } from 'lucide-react';
import { useChatStore } from '@/stores';
import { ModeSelector, QualityBadge } from './ModeSelector';
import { generateId } from '@/lib/utils';
import type { Message } from '@/types';
import { askQuestion } from '@/lib/api';

export function ChatInput() {
  const [input, setInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastQuality, setLastQuality] = useState<Message['quality']>(undefined);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { addMessage, setLoading, mode, setMode } = useChatStore();

  const handleSubmit = async () => {
    if (!input.trim() || isSubmitting) return;

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput('');
    setIsSubmitting(true);
    setLoading(true);

    const startTime = Date.now();

    try {
      const response = await askQuestion({
        question: userMessage.content,
        n_results: 5,
        temperature: 0.3,
        mode: mode as 'strict' | 'balanced' | 'explorative',
        include_quality: true,
      });

      const latency = (Date.now() - startTime) / 1000;
      setLastQuality(response.quality);

      const aiMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: response.answer || 'Maaf, saya tidak dapat menjawab pertanyaan tersebut.',
        timestamp: new Date(),
        sources: response.sources,
        latency,
        quality: response.quality,
        enrichment: response.enrichment,
      };

      addMessage(aiMessage);
    } catch (error) {
      const errorMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: 'Terjadi kesalahan saat memproses pertanyaan. Silakan coba lagi.',
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setIsSubmitting(false);
      setLoading(false);
    }
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
    target.style.height = Math.min(target.scrollHeight, 200) + 'px';
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      {/* Mode Selector */}
      <div className="flex items-center justify-between mb-3">
        <ModeSelector value={mode} onChange={setMode} />
        <QualityBadge quality={lastQuality} />
      </div>

      <div className="relative">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={`Ask in ${mode} mode... (Cmd+Enter to send)`}
          className="w-full bg-[var(--bg-elevated)] text-[var(--text-primary)] rounded-xl
                     border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none
                     pl-4 pr-14 py-3 min-h-[56px] max-h-[200px] resize-none
                     placeholder-[var(--text-muted)] transition-colors"
          rows={1}
          disabled={isSubmitting}
        />
        
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || isSubmitting}
          className="absolute right-3 bottom-3 p-2 rounded-lg
                     bg-[var(--accent)] text-white
                     hover:bg-[var(--accent-hover)] disabled:opacity-50
                     disabled:cursor-not-allowed transition-colors"
        >
          <Send size={18} />
        </button>
      </div>
      
      <div className="mt-2 flex items-center justify-between text-xs text-[var(--text-muted)]">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 rounded bg-[var(--bg-elevated)]">Cmd</kbd>
            <kbd className="px-1.5 py-0.5 rounded bg-[var(--bg-elevated)]">K</kbd>
            <span>to focus</span>
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 rounded bg-[var(--bg-elevated)]">Enter</kbd>
            <span>to send</span>
          </span>
        </div>
        
        {/* Mode description */}
        <span className="italic">
          {mode === 'strict' && 'Factual only - no assumptions'}
          {mode === 'balanced' && 'Data + reasonable connections'}
          {mode === 'explorative' && 'Broader analysis with confidence markers'}
        </span>
      </div>
    </div>
  );
}
