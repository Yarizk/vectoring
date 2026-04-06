import { create } from 'zustand';
import type { DataSource, IngestionRun, PipelineStats } from '@/types';

interface PipelineState {
  stats: PipelineStats | null;
  dataSources: DataSource[];
  ingestionHistory: IngestionRun[];
  isIngesting: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setStats: (stats: PipelineStats) => void;
  setDataSources: (sources: DataSource[]) => void;
  setIngestionHistory: (history: IngestionRun[]) => void;
  setIngesting: (ingesting: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const usePipelineStore = create<PipelineState>((set) => ({
  stats: null,
  dataSources: [],
  ingestionHistory: [],
  isIngesting: false,
  isLoading: false,
  error: null,
  
  setStats: (stats) => set({ stats }),
  setDataSources: (sources) => set({ dataSources: sources }),
  setIngestionHistory: (history) => set({ ingestionHistory: history }),
  setIngesting: (ingesting) => set({ isIngesting: ingesting }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));
