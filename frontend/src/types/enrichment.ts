export interface ForeignFlow {
  ticker: string;
  foreign_buy: number;
  foreign_sell: number;
  foreign_net: number;
}

export interface PricePerformanceData {
  ticker: string;
  performance_1w: number | null;
  performance_1m: number | null;
  performance_3m: number | null;
  performance_6m: number | null;
  performance_ytd: number | null;
  performance_1y: number | null;
}

export interface CorpAction {
  ticker: string;
  action_type: string;
  description: string;
  ex_date: string | null;
  announcement_date: string | null;
}

export interface TickerEnrichment {
  foreign_flow: ForeignFlow | null;
  price_performance: PricePerformanceData | null;
  corp_actions: CorpAction[];
}

export type EnrichmentData = Record<string, TickerEnrichment>;
