import { API_BASE_URL } from './constants';
import type {
  AskRequest,
  AskResponse,
  HealthResponse,
  ResponseMode,
} from '@/types';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error);
  }
  
  return response.json();
}

// Health check
export async function checkHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>('/health');
}

// Stats
export async function getStats(): Promise<PipelineStats> {
  return fetchApi<PipelineStats>('/stats');
}

// Ask question
export async function askQuestion(
  request: AskRequest
): Promise<AskResponse> {
  return fetchApi<AskResponse>('/ask', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Get response modes
export async function getModes(): Promise<Record<string, ResponseMode>> {
  const response = await fetchApi<{ modes: Record<string, ResponseMode> }>('/modes');
  return response.modes;
}

// Ingestion
export async function triggerIngestion(
  clearExisting = false
): Promise<{ success: boolean; message: string }> {
  return fetchApi('/ingest', {
    method: 'POST',
    body: JSON.stringify({ clear_existing: clearExisting }),
  });
}

export async function getIngestionStatus(): Promise<{
  running: boolean;
  last_result: any;
}> {
  return fetchApi('/ingest/status');
}

// Market data (Stockbit integration)
export async function getMarketData(
  ticker: string
): Promise<{ ticker: string; enrichment: any; available: boolean } | null> {
  try {
    return await fetchApi(`/api/ticker/${ticker.toUpperCase()}`);
  } catch {
    return null;
  }
}

export async function getBatchMarketData(
  tickers: string[]
): Promise<Record<string, any>> {
  const results: Record<string, any> = {};
  await Promise.all(
    tickers.map(async (ticker) => {
      const data = await getMarketData(ticker);
      if (data?.available) {
        results[ticker] = data.enrichment;
      }
    })
  );
  return results;
}

// Chart data
export interface OhlcvBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  value: number;
  net_foreign: number;
}

export async function getOhlcvChart(
  ticker: string,
  days = 90
): Promise<{ ticker: string; data: OhlcvBar[]; count: number }> {
  return fetchApi(`/api/chart/${ticker.toUpperCase()}/ohlcv?days=${days}`);
}

export async function getFundamentals(
  ticker: string
): Promise<{ ticker: string; data: Record<string, any> }> {
  return fetchApi(`/api/chart/${ticker.toUpperCase()}/fundamentals`);
}

export { ApiError };
