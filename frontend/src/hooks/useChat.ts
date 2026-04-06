import { useCallback, useState } from 'react';
import { useChatStore } from '@/stores';
import { askQuestion } from '@/lib/api';
import { generateId } from '@/lib/utils';
import type { Message } from '@/types';

export function useChat() {
  const { messages, addMessage, setLoading, mode } = useChatStore();
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;

      // Add user message
      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      };

      addMessage(userMessage);
      setLoading(true);
      setError(null);

      const startTime = Date.now();

      try {
        // Use the current mode from the store
        const response = await askQuestion({
          question: userMessage.content,
          n_results: 5,
          temperature: 0.3,
          mode: mode as 'strict' | 'balanced' | 'explorative',
          include_quality: true,
        });

        const latency = (Date.now() - startTime) / 1000;

        const aiMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: response.answer || 'Maaf, saya tidak dapat menjawab pertanyaan tersebut.',
          timestamp: new Date(),
          sources: response.sources,
          latency,
          mode: response.mode,
          quality: response.quality,
        };

        addMessage(aiMessage);
        return aiMessage;
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMsg);

        const errorMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: `Error: ${errorMsg}`,
          timestamp: new Date(),
        };
        addMessage(errorMessage);
        return errorMessage;
      } finally {
        setLoading(false);
      }
    },
    [addMessage, setLoading, mode]  // Include mode in dependencies
  );

  return {
    messages,
    sendMessage,
    error,
    clearError: () => setError(null),
  };
}
