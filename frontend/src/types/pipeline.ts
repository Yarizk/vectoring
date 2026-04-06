export interface DataSource {
  id: string;
  name: string;
  type: 'ksei_pdf' | 'ksei_json' | 'market_data';
  status: 'ok' | 'warning' | 'error';
  documentCount: number;
  chunkCount: number;
  lastUpdate: string;
  isFresh: boolean;
}

export interface IngestionRun {
  id: string;
  timestamp: string;
  source: string;
  documentsProcessed: number;
  chunksCreated: number;
  status: 'success' | 'partial' | 'error';
  errors?: string[];
  duration?: number;
}

export interface PipelineStats {
  collectionName: string;
  documentCount: number;
  embeddingModel: string;
  llmProvider: string;
  ollamaStatus: boolean;
  jatevoStatus: boolean;
  jatevoModel: string;
  availableModels: string[];
  configErrors: string[];
}
