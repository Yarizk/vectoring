import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatNumber(num: number, decimals = 2): string {
  if (num >= 1e12) return (num / 1e12).toFixed(decimals) + 'T';
  if (num >= 1e9) return (num / 1e9).toFixed(decimals) + 'B';
  if (num >= 1e6) return (num / 1e6).toFixed(decimals) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(decimals) + 'K';
  return num.toFixed(decimals);
}

export function formatPercentage(value: number, showSign = true): string {
  const sign = showSign && value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

export function formatChange(value: number): { text: string; isPositive: boolean } {
  return {
    text: formatPercentage(value),
    isPositive: value >= 0,
  };
}

export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(date: string | Date): string {
  const d = new Date(date);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(date);
}

export function extractTickers(text: string): string[] {
  const excludeWords = new Set([
    'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'ANY', 'CAN',
    'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM',
    'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY',
    'WHO', 'BOY', 'DID', 'EYE', 'SAW', 'SHE', 'TOO', 'USE', 'DAN', 'YANG',
    'UNTUK', 'DENGAN', 'DARI', 'INI', 'DALAM', 'PADA', 'ADALAH', 'SEBAGAI',
    'ATAU', 'JUGA', 'OLEH', 'SAHAM', 'BESAR', 'TERBESAR', 'PEMEGANG', 'PEMILIK',
    'APA', 'SIAPA', 'BAGAIMANA', 'KAPAN', 'DIMANA', 'MENGAPA', 'COMPARE',
    'WHAT', 'WHEN', 'WHERE', 'WHY', 'PRICE', 'ABOUT', 'THAT', 'WITH',
  ]);
  
  const pattern = /\b([A-Z]{2,5})\b/g;
  const matches = text.toUpperCase().match(pattern) || [];
  
  return [...new Set(matches.filter((m) => !excludeWords.has(m)))];
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}
