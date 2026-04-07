import type { EnrichmentData } from './enrichment';

export interface Source {
  id: string;
  source: 'ksei_pdf' | 'ksei_json' | 'market_data';
  text_preview: string;
  distance: number;
  // KSEI JSON specific
  ticker?: string;
  date?: string;
  chunk_type?: string;
  // KSEI PDF specific
  filename?: string;
  page_number?: number;
  month_year?: string;
  // Metadata
  metadata?: Record<string, any>;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  latency?: number;
  isLoading?: boolean;
  mode?: string;
  quality?: {
    quality_score: number;
    coverage: string;
    gaps: string[];
    recommendations: string[];
  };
  enrichment?: EnrichmentData;
}

export interface ChatResponse {
  question: string;
  answer: string | null;
  sources: Source[];
  success: boolean;
  error?: string;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  prompt: string;
}
