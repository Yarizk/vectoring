import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Message, Source, TickerDetail } from '@/types';

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  selectedSources: Source[];
  selectedTicker: TickerDetail | null;
  mode: string;
  
  // Actions
  addMessage: (message: Message) => void;
  setLoading: (loading: boolean) => void;
  clearChat: () => void;
  setSelectedSources: (sources: Source[]) => void;
  setSelectedTicker: (ticker: TickerDetail | null) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setMode: (mode: string) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      isLoading: false,
      selectedSources: [],
      selectedTicker: null,
      mode: 'balanced',
      
      addMessage: (message) => set((state) => ({
        messages: [...state.messages, message],
      })),
      
      setLoading: (loading) => set({ isLoading: loading }),
      
      clearChat: () => set({ 
        messages: [],
        selectedSources: [],
        selectedTicker: null,
      }),
      
      setSelectedSources: (sources) => set({ selectedSources: sources }),
      
      setSelectedTicker: (ticker) => set({ selectedTicker: ticker }),
      
      updateMessage: (id, updates) => set((state) => ({
        messages: state.messages.map((m) =>
          m.id === id ? { ...m, ...updates } : m
        ),
      })),
      
      setMode: (mode) => set({ mode }),
    }),
    {
      name: 'ksei-chat-storage',
      partialize: (state) => ({ 
        messages: state.messages,
        mode: state.mode,
      }),
    }
  )
);
