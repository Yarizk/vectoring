export const COLORS = {
  bg: {
    primary: '#0a0b0f',
    surface: '#12141a',
    surfaceHover: '#1a1d27',
    elevated: '#1e2130',
  },
  border: {
    default: '#1e2130',
    hover: '#2a2e42',
  },
  text: {
    primary: '#e4e6ef',
    secondary: '#6b7194',
    muted: '#4b5169',
  },
  accent: {
    blue: '#3b82f6',
    blueHover: '#2563eb',
    green: '#22c55e',
    red: '#ef4444',
    gold: '#f59e0b',
    purple: '#8b5cf6',
  },
} as const;

export const QUICK_ACTIONS = [
  {
    id: 'top-foreign-drops',
    label: 'Top Foreign Drops',
    icon: 'TrendingDown',
    prompt: 'Which stocks had the biggest foreign ownership drop this month?',
  },
  {
    id: 'banking-overview',
    label: 'Banking Overview',
    icon: 'Building2',
    prompt: 'Compare foreign ownership of major banking stocks (BBCA, BBRI, BMRI, BBNI)',
  },
  {
    id: 'search-by-investor',
    label: 'Search by Investor',
    icon: 'Users',
    prompt: 'Which stocks does BlackRock have significant holdings in?',
  },
  {
    id: 'sector-breakdown',
    label: 'Sector Breakdown',
    icon: 'PieChart',
    prompt: 'What is the foreign ownership distribution across different sectors?',
  },
] as const;

export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
