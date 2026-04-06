import { useState, useCallback } from 'react';
import { getMarketData } from '@/lib/api';
import type { TickerDetail } from '@/types';

export function useTicker() {
  const [ticker, setTicker] = useState<TickerDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTicker = useCallback(async (symbol: string) => {
    try {
      setIsLoading(true);
      setError(null);

      // For now, return mock data
      // In the future, this will call the actual API
      const mockTicker: TickerDetail = {
        symbol,
        name: getCompanyName(symbol),
        sector: 'Banking',
        index: ['IDX30', 'LQ45'],
        price: 4520,
        pe: 12.4,
        pbv: 2.1,
        ownership: [
          { category: 'Pemerintah RI', percentage: 53.2 },
          { category: 'Foreign', percentage: 24.1 },
          { category: 'Domestic Public', percentage: 22.7 },
        ],
        topHolders: [
          { name: 'Danantara Asset Management', percentage: 52.66, type: 'Institution' },
          { name: 'Indonesia Investment Authority', percentage: 3.63, type: 'Institution' },
          { name: 'Employees Provident Fund', percentage: 1.14, type: 'Foreign' },
        ],
        momChanges: {
          foreign: -0.3,
          domestic: 0.3,
        },
        lastUpdate: new Date().toISOString(),
      };

      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 500));
      
      setTicker(mockTicker);
      return mockTicker;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch ticker');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearTicker = useCallback(() => {
    setTicker(null);
    setError(null);
  }, []);

  return {
    ticker,
    isLoading,
    error,
    fetchTicker,
    clearTicker,
  };
}

function getCompanyName(symbol: string): string {
  const names: Record<string, string> = {
    BBRI: 'Bank Rakyat Indonesia',
    BBCA: 'Bank Central Asia',
    BMRI: 'Bank Mandiri',
    BBNI: 'Bank Negara Indonesia',
    GOTO: 'GoTo Gojek Tokopedia',
    TLKM: 'Telkom Indonesia',
    ASII: 'Astra International',
    UNVR: 'Unilever Indonesia',
  };
  return names[symbol] || `${symbol} Tbk`;
}
