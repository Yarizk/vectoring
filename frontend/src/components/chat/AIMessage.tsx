import { useState, useMemo } from 'react';
import {
  Bot, FileText, Database, Clock, ChevronDown, ChevronUp,
  AlertTriangle, CheckCircle, HelpCircle, BarChart3,
  Building2, Copy, Check,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChatStore, useUIStore } from '@/stores';
import { formatDate } from '@/lib/utils';
import type { Message, Source } from '@/types';
import { MarketContext } from './MarketContext';

interface AIMessageProps {
  message: Message;
}

const CHUNK_LABELS: Record<string, string> = {
  ticker_summary: 'KSEI Summary',
  holder_focus: 'KSEI Holder',
  pdf_page: 'PDF',
  company_profile: 'Company',
  financial_ratios: 'Ratios',
  analyst_consensus: 'Analyst',
  major_holders_stockbit: 'Holders',
  sbitools_company: 'Company',
  sbitools_fundamentals: 'Ratios',
  sbitools_financials: 'Financials',
  sbitools_analyst: 'Analyst',
  sbitools_corporate_actions: 'Corp Actions',
  sbitools_holders: 'Holders',
  sbitools_price_perf: 'Price Perf.',
};

function SourceRow({ source }: { source: Source }) {
  const chunkType = source.chunk_type ?? '';
  const isStockbit = source.source === 'sbitools' || chunkType.startsWith('sbitools_') || chunkType.startsWith('company_');

  const icon = source.source === 'ksei_pdf'
    ? <FileText size={12} className="text-[var(--accent-gold)]" />
    : isStockbit
      ? <Building2 size={12} className="text-[var(--accent-purple)]" />
      : <Database size={12} className="text-[var(--accent-green)]" />;

  const label = source.source === 'ksei_pdf'
    ? `${source.filename ?? 'PDF'}, p.${source.page_number}`
    : source.ticker
      ? `${source.ticker}${chunkType ? ' · ' + (CHUNK_LABELS[chunkType] ?? chunkType) : ''}`
      : chunkType || source.source;

  return (
    <div className="flex items-start gap-1.5 text-xs">
      <div className="mt-0.5 flex-shrink-0">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-[var(--text-secondary)] truncate">{label}</span>
          <span className="text-[var(--accent)] flex-shrink-0 font-medium">
            {Math.round((1 - source.distance) * 100)}%
          </span>
        </div>
        <p className="text-[var(--text-muted)] truncate">{source.text_preview?.slice(0, 90)}</p>
      </div>
    </div>
  );
}

export function AIMessage({ message }: AIMessageProps) {
  const { setSelectedSources, selectedChartTicker, setSelectedChartTicker } = useChatStore();
  const { setRightPanelOpen } = useUIStore();
  const [showSources, setShowSources] = useState(true);
  const [showQuality, setShowQuality] = useState(false);
  const [copied, setCopied] = useState(false);

  // Extract unique tickers from sources + enrichment
  const detectedTickers = useMemo(() => {
    const tickers = new Set<string>();
    message.sources?.forEach(s => { if (s.ticker) tickers.add(s.ticker); });
    if (message.enrichment) Object.keys(message.enrichment).forEach(t => tickers.add(t));
    return Array.from(tickers).sort();
  }, [message.sources, message.enrichment]);

  const handleSourceClick = () => {
    if (message.sources) {
      setSelectedSources(message.sources);
      setRightPanelOpen(true);
    }
  };

  const handleViewChart = (ticker: string) => {
    setSelectedChartTicker(ticker === selectedChartTicker ? null : ticker);
    setRightPanelOpen(true);
  };

  const handleCopy = async () => {
    if (!message.content) return;
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const hasCertain = message.content?.includes('[CERTAIN]');
  const hasInferred = message.content?.includes('[INFERRED]');
  const hasUncertain = message.content?.includes('[UNCERTAIN]') || message.content?.includes('[NOT_AVAILABLE]');
  const hasBeyond = message.content?.includes('[BEYOND_DATA]');

  return (
    <div className="px-4 py-3 bg-[var(--bg-surface)] border-b border-[var(--border)] group animate-fade-in">
      <div className="flex gap-3 max-w-4xl mx-auto">
        {/* Avatar */}
        <div className="flex-shrink-0 w-6 h-6 rounded bg-[var(--accent)] flex items-center justify-center mt-0.5">
          <Bot size={13} className="text-white" />
        </div>

        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="text-xs font-semibold text-[var(--text-primary)]">KSEI Intelligence</span>
            <span className="text-xs text-[var(--text-muted)]">{formatDate(message.timestamp)}</span>
            {message.latency && (
              <span className="text-xs text-[var(--text-muted)] flex items-center gap-0.5">
                <Clock size={10} />
                {message.latency.toFixed(1)}s
              </span>
            )}
            {message.mode && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-muted)] capitalize">
                {message.mode}
              </span>
            )}
            {hasCertain && (
              <span className="flex items-center gap-0.5 text-xs text-green-400">
                <CheckCircle size={10} /> Factual
              </span>
            )}
            {hasInferred && (
              <span className="flex items-center gap-0.5 text-xs text-blue-400">
                <HelpCircle size={10} /> Inferred
              </span>
            )}
            {hasUncertain && (
              <span className="flex items-center gap-0.5 text-xs text-yellow-400">
                <AlertTriangle size={10} /> Uncertain
              </span>
            )}
            {hasBeyond && (
              <span className="flex items-center gap-0.5 text-xs text-purple-400">
                <HelpCircle size={10} /> Beyond
              </span>
            )}
            <button
              onClick={handleCopy}
              className="ml-auto flex items-center gap-1 text-xs text-[var(--text-muted)]
                         hover:text-[var(--text-primary)] transition-colors opacity-0 group-hover:opacity-100"
            >
              {copied ? <Check size={11} className="text-green-400" /> : <Copy size={11} />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>

          {/* Market Context Cards */}
          {message.enrichment && Object.keys(message.enrichment).length > 0 && (
            <MarketContext enrichment={message.enrichment} />
          )}

          {/* Markdown Content */}
          <div className="prose prose-invert max-w-none text-sm text-[var(--text-primary)] leading-relaxed markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                strong: ({ children }) => {
                  const text = String(children);
                  if (text === '[CERTAIN]') return <span className="text-green-400 font-semibold text-xs">[CERTAIN]</span>;
                  if (text === '[INFERRED]') return <span className="text-blue-400 font-semibold text-xs">[INFERRED]</span>;
                  if (text === '[UNCERTAIN]') return <span className="text-yellow-400 font-semibold text-xs">[UNCERTAIN]</span>;
                  if (text === '[NOT_AVAILABLE]') return <span className="text-red-400 font-semibold text-xs">[NOT_AVAILABLE]</span>;
                  if (text === '[BEYOND_DATA]') return <span className="text-purple-400 font-semibold text-xs">[BEYOND_DATA]</span>;
                  return <strong>{children}</strong>;
                },
                code: ({ children, className }) => {
                  const isInline = !className;
                  if (isInline) {
                    return <code className="bg-[var(--bg-elevated)] px-1 py-0.5 rounded text-[0.8em] font-mono text-[var(--accent-gold)]">{children}</code>;
                  }
                  return <code className={className}>{children}</code>;
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Ticker chart chips */}
          {detectedTickers.length > 0 && (
            <div className="mt-2.5 flex items-center gap-1.5 flex-wrap">
              <BarChart3 size={12} className="text-[var(--text-muted)]" />
              <span className="text-xs text-[var(--text-muted)]">Chart:</span>
              {detectedTickers.map(ticker => (
                <button
                  key={ticker}
                  onClick={() => handleViewChart(ticker)}
                  title={`View ${ticker} chart`}
                  className={[
                    'px-2 py-0.5 rounded text-xs font-mono font-semibold transition-all border',
                    selectedChartTicker === ticker
                      ? 'bg-[var(--accent)] text-white border-[var(--accent)]'
                      : 'bg-[var(--bg-elevated)] text-[var(--accent)] border-[var(--border)] hover:bg-[var(--accent)] hover:text-white hover:border-[var(--accent)]',
                  ].join(' ')}
                >
                  {ticker}
                </button>
              ))}
            </div>
          )}

          {/* Footer: quality + sources */}
          <div className="mt-2 pt-2 border-t border-[var(--border)] flex items-center gap-3 flex-wrap">
            {message.quality && (
              <button
                onClick={() => setShowQuality(!showQuality)}
                className="flex items-center gap-1 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              >
                {showQuality ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                Quality: {message.quality.quality_score}% · {message.quality.coverage}
              </button>
            )}
            {message.sources && message.sources.length > 0 && (
              <>
                <button
                  onClick={handleSourceClick}
                  className="flex items-center gap-1 px-2 py-0.5 rounded text-xs
                             bg-[var(--bg-elevated)] text-[var(--text-secondary)]
                             hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)]
                             transition-colors"
                >
                  <FileText size={11} />
                  {message.sources.length} sources
                </button>
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="flex items-center gap-0.5 text-xs text-[var(--text-muted)]
                             hover:text-[var(--text-primary)] transition-colors"
                >
                  {showSources ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                  {showSources ? 'Hide' : 'Show'}
                </button>
              </>
            )}
          </div>

          {/* Quality details */}
          {showQuality && message.quality && (
            <div className="mt-1.5 p-2 rounded bg-[var(--bg-elevated)] text-xs space-y-0.5">
              {message.quality.gaps.map((gap, i) => (
                <div key={i} className="text-yellow-400 flex items-center gap-1">
                  <AlertTriangle size={10} /> {gap}
                </div>
              ))}
              {message.quality.recommendations.map((rec, i) => (
                <div key={i} className="text-[var(--text-secondary)] flex items-center gap-1">
                  <CheckCircle size={10} className="text-[var(--accent)]" /> {rec}
                </div>
              ))}
            </div>
          )}

          {/* Sources inline */}
          {showSources && message.sources && message.sources.length > 0 && (
            <div className="mt-1.5 space-y-1">
              {message.sources.slice(0, 4).map(source => (
                <SourceRow key={source.id} source={source} />
              ))}
              {message.sources.length > 4 && (
                <button
                  onClick={handleSourceClick}
                  className="text-xs text-[var(--accent)] hover:underline"
                >
                  +{message.sources.length - 4} more — view in panel
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
