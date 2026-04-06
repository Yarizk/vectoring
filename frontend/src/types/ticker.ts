export interface Ticker {
  symbol: string;
  name: string;
  sector?: string;
  index?: string[]; // IDX30, LQ45, etc.
}

export interface OwnershipBreakdown {
  category: string;
  percentage: number;
  change?: number;
}

export interface TickerDetail extends Ticker {
  // Market data (placeholder for Stockbit)
  price?: number;
  change?: number;
  changePercent?: number;
  pe?: number;
  pbv?: number;
  marketCap?: number;
  
  // Ownership data
  ownership: OwnershipBreakdown[];
  topHolders: Holder[];
  
  // MoM changes
  momChanges: {
    foreign: number;
    domestic: number;
  };
  
  // Last update
  lastUpdate: string;
}

export interface Holder {
  name: string;
  percentage: number;
  type: string; // 'Institution', 'Individual', 'Foreign', etc.
  domicile?: string;
  change?: number;
}
