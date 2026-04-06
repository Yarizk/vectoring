import { useCallback, useEffect, useState } from 'react';
import { checkHealth, getStats, triggerIngestion } from '@/lib/api';
import type { PipelineStats, DataSource, IngestionRun } from '@/types';

export function usePipeline() {
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [ingestionHistory, setIngestionHistory] = useState<IngestionRun[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Check health
      const health = await checkHealth();

      // Get stats
      const statsData = await getStats();
      setStats(statsData);

      // Build data sources
      const sources: DataSource[] = [
        {
          id: 'ksei-json',
          name: 'KSEI JSON',
          type: 'ksei_json',
          status: 'ok',
          documentCount: Math.floor(statsData.documentCount * 0.8),
          chunkCount: Math.floor(statsData.documentCount * 0.8),
          lastUpdate: new Date().toISOString(),
          isFresh: true,
        },
        {
          id: 'ksei-pdf',
          name: 'KSEI PDF',
          type: 'ksei_pdf',
          status: 'ok',
          documentCount: Math.floor(statsData.documentCount * 0.15),
          chunkCount: Math.floor(statsData.documentCount * 0.15),
          lastUpdate: new Date().toISOString(),
          isFresh: true,
        },
        {
          id: 'market-data',
          name: 'Market Data',
          type: 'market_data',
          status: 'warning',
          documentCount: 0,
          chunkCount: 0,
          lastUpdate: new Date(Date.now() - 86400000 * 2).toISOString(),
          isFresh: false,
        },
      ];
      setDataSources(sources);

      // Mock ingestion history
      setIngestionHistory([
        {
          id: '1',
          timestamp: new Date().toISOString(),
          source: 'KSEI JSON',
          documentsProcessed: 955,
          chunksCreated: 16380,
          status: 'success',
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 86400000).toISOString(),
          source: 'KSEI PDF',
          documentsProcessed: 2,
          chunksCreated: 2923,
          status: 'success',
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pipeline data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const ingest = useCallback(
    async (clearExisting = false) => {
      try {
        setIsIngesting(true);
        setError(null);
        await triggerIngestion(clearExisting);
        // Refresh after ingestion
        setTimeout(fetchData, 2000);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ingestion failed');
      } finally {
        setIsIngesting(false);
      }
    },
    [fetchData]
  );

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return {
    stats,
    dataSources,
    ingestionHistory,
    isLoading,
    isIngesting,
    error,
    refresh: fetchData,
    ingest,
  };
}
