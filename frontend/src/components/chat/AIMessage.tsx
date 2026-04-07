import { useState } from 'react';
import { Bot, FileText, Database, Clock, ChevronDown, ChevronUp, AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChatStore, useUIStore } from '@/stores';
import { formatDate } from '@/lib/utils';
import type { Message, Source } from '@/types';
import { MarketContext } from './MarketContext';

interface AIMessageProps {
  message: Message;
}

export function AIMessage({ message }: AIMessageProps) {
  const { setSelectedSources } = useChatStore();
  const { setRightPanelOpen } = useUIStore();
  const [showSources, setShowSources] = useState(true);
  const [showQuality, setShowQuality] = useState(false);

  const handleSourceClick = () => {
    if (message.sources) {
      setSelectedSources(message.sources);
      setRightPanelOpen(true);
    }
  };

  // Parse confidence markers from content
  const hasCertainMarkers = message.content?.includes('[CERTAIN]');
  const hasInferredMarkers = message.content?.includes('[INFERRED]');
  const hasUncertainMarkers = message.content?.includes('[UNCERTAIN]') || message.content?.includes('[NOT_AVAILABLE]');
  const hasBeyondData = message.content?.includes('[BEYOND_DATA]');

  return (
    <div className="px-4 py-3 bg-[var(--bg-surface)] border-b border-[var(--border)]">
      <div className="flex gap-3 max-w-4xl mx-auto">
        <div className="flex-shrink-0 w-6 h-6 rounded bg-[var(--accent)]
                        flex items-center justify-center">
          <Bot size={13} className="text-white" />
        </div>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-medium text-[var(--text-primary)]">KSEI Intelligence</span>
            <span className="text-xs text-[var(--text-muted)]">
              {formatDate(message.timestamp)}
            </span>
            {message.latency && (
              <span className="text-xs text-[var(--text-muted)] flex items-center gap-0.5">
                <Clock size={11} />
                {message.latency.toFixed(1)}s
              </span>
            )}
            {message.mode && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-muted)] capitalize">
                {message.mode}
              </span>
            )}
            {/* Confidence indicators inline */}
            {hasCertainMarkers && (
              <span className="flex items-center gap-0.5 text-xs text-green-400">
                <CheckCircle size={11} /> Factual
              </span>
            )}
            {hasInferredMarkers && (
              <span className="flex items-center gap-0.5 text-xs text-blue-400">
                <HelpCircle size={11} /> Inferred
              </span>
            )}
            {hasUncertainMarkers && (
              <span className="flex items-center gap-0.5 text-xs text-yellow-400">
                <AlertTriangle size={11} /> Uncertain
              </span>
            )}
            {hasBeyondData && (
              <span className="flex items-center gap-0.5 text-xs text-purple-400">
                <HelpCircle size={11} /> Beyond
              </span>
            )}
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
                }
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Data Quality + Sources footer */}
          <div className="mt-2 pt-2 border-t border-[var(--border)] flex items-center gap-3 flex-wrap">
            {message.quality && (
              <>
                <button
                  onClick={() => setShowQuality(!showQuality)}
                  className="flex items-center gap-1 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                >
                  {showQuality ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  Quality: {message.quality.quality_score}% · {message.quality.coverage}
                </button>
              </>
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
                  <FileText size={12} />
                  {message.sources.length} sources
                </button>

                <button
                  onClick={() => setShowSources(!showSources)}
                  className="flex items-center gap-0.5 text-xs text-[var(--text-muted)]
                             hover:text-[var(--text-primary)] transition-colors"
                >
                  {showSources ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  {showSources ? 'Hide' : 'Show'}
                </button>
              </>
            )}
          </div>

          {showQuality && message.quality && (
            <div className="mt-1.5 p-2 rounded bg-[var(--bg-elevated)] text-xs space-y-1">
              {message.quality.gaps.map((gap, i) => (
                <div key={i} className="text-yellow-400">· {gap}</div>
              ))}
              {message.quality.recommendations.map((rec, i) => (
                <div key={i} className="text-[var(--text-secondary)]">· {rec}</div>
              ))}
            </div>
          )}

          {showSources && message.sources && message.sources.length > 0 && (
            <div className="mt-1.5 grid gap-1.5">
              {message.sources.slice(0, 3).map((source, idx) => (
                <SourceRow key={source.id} source={source} index={idx + 1} />
              ))}
              {message.sources.length > 3 && (
                <div className="text-xs text-[var(--text-muted)]">
                  +{message.sources.length - 3} more
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SourceRow({ source }: { source: Source; index: number }) {
  const getIcon = () => {
    switch (source.source) {
      case 'ksei_pdf':
        return <FileText size={12} className="text-[var(--accent-gold)]" />;
      case 'ksei_json':
        return <Database size={12} className="text-[var(--accent-green)]" />;
      default:
        return <Database size={12} className="text-[var(--text-muted)]" />;
    }
  };

  const getLabel = () => {
    if (source.source === 'ksei_pdf') {
      return `${source.filename}, p.${source.page_number}`;
    }
    if (source.source === 'ksei_json') {
      return `${source.ticker} · ${source.date}`;
    }
    return 'Unknown source';
  };

  return (
    <div className="flex items-start gap-1.5 text-xs">
      <div className="mt-0.5 flex-shrink-0">{getIcon()}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-[var(--text-secondary)] truncate">{getLabel()}</span>
          <span className="text-[var(--accent)] flex-shrink-0">
            {Math.round((1 - source.distance) * 100)}%
          </span>
        </div>
        <p className="text-[var(--text-muted)] truncate">
          {source.text_preview?.slice(0, 90)}
        </p>
      </div>
    </div>
  );
}
