export interface ApiResponse<T> {
  data?: T;
  error?: string;
  success: boolean;
}

export interface AskRequest {
  question: string;
  n_results?: number;
  temperature?: number;
  ticker?: string;
  mode?: 'strict' | 'balanced' | 'explorative';
  include_quality?: boolean;
}

export interface DataQuality {
  has_data: boolean;
  quality_score: number;
  coverage: 'none' | 'minimal' | 'partial' | 'complete';
  sources: { pdf: boolean; json: boolean };
  tickers_found: string[];
  tickers_requested: string[];
  tickers_matched: string[];
  gaps: string[];
  recommendations: string[];
}

export interface AskResponse {
  question: string;
  answer: string | null;
  sources: any[];
  quality?: DataQuality;
  mode: string;
  success: boolean;
  error?: string;
}

export interface ResponseMode {
  description: string;
  temperature: number;
  creativity: number;
  allow_inference: boolean;
  allow_general_knowledge: boolean;
}

export interface HealthResponse {
  status: string;
  provider: string;
  provider_connected: boolean;
  config_errors: string[];
}

export { ResponseMode };
