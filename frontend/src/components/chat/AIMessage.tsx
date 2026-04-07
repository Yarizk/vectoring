import { useState } from 'react';
import { Bot, FileText, Database, Clock, ChevronDown, ChevronUp, AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChatStore, useUIStore } from '@/stores';
import { cn, formatDate } from '@/lib/utils';
import type { Message, Source } from '@/types';
import { MarketContext } from './MarketContext';

interface AIMessageProps {
  message: Message;
}

export function AIMessage({ message }: AIMessageProps) {
  const { setSelectedSources, setSelectedTicker } = useChatStore();
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
    <div className="px-4 py-6 bg-[var(--bg-surface)] border-b border-[var(--border)]">
      <div className="flex gap-4 max-w-4xl mx-auto">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-[var(--accent)] 
                        flex items-center justify-center">
          <Bot size={16} className="text-white" />
        </div>
        
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-[var(--text-primary)]">KSEI Intelligence</span>
            <span className="text-xs text-[var(--text-muted)]">
              {formatDate(message.timestamp)}
            </span>
            {message.latency && (
              <span className="text-xs text-[var(--text-muted)] flex items-center gap-1">
                <Clock size={12} />
                {message.latency.toFixed(1)}s
              </span>
            )}
            {message.mode && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-muted)] capitalize">
                {message.mode}
              </span>
            )}
          </div>
          
          {/* Confidence Indicators */}
          {(hasCertainMarkers || hasInferredMarkers || hasUncertainMarkers || hasBeyondData) && (
            <div className="flex flex-wrap gap-2 mb-3">
              {hasCertainMarkers && (
                <span className="flex items-center gap-1 text-xs text-green-400">
                  <CheckCircle size={12} /> Factual Data
                </span>
              )}
              {hasInferredMarkers && (
                <span className="flex items-center gap-1 text-xs text-blue-400">
                  <HelpCircle size={12} /> Inferred
                </span>
              )}
              {hasUncertainMarkers && (
                <span className="flex items-center gap-1 text-xs text-yellow-400">
                  <AlertTriangle size={12} /> Uncertain
                </span>
              )}
              {hasBeyondData && (
                <span className="flex items-center gap-1 text-xs text-purple-400">
                  <HelpCircle size={12} /> Beyond Data
                </span>
              )}
            </div>
          )}
          
          {/* Market Context Cards */}
          {message.enrichment && Object.keys(message.enrichment).length > 0 && (
            <MarketContext enrichment={message.enrichment} />
          )}

          {/* Markdown Content */}
          <div className="prose prose-invert max-w-none text-[var(--text-primary)] leading-relaxed">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                // Custom renderers for confidence markers
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
          
          {/* Data Quality Section */}
          {message.quality && (
            <div className="mt-4 pt-4 border-t border-[var(--border)]">
              <button
                onClick={() => setShowQuality(!showQuality)}
                className="flex items-center gap-2 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                {showQuality ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Data Quality: {message.quality.quality_score}% ({message.quality.coverage})
              </button>
              
              {showQuality && (
                <div className="mt-2 p-3 rounded-lg bg-[var(--bg-elevated)] text-sm">
                  {message.quality.gaps.length > 0 && (
                    <div className="mb-2">
                      <span className="text-[var(--text-muted)]">Gaps:</span>
                      <ul className="mt-1 space-y-1">
                        {message.quality.gaps.map((gap, i) => (
                          <li key={i} className="text-yellow-400">• {gap}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {message.quality.recommendations.length > 0 && (
                    <div>
                      <span className="text-[var(--text-muted)]">Suggestions:</span>
                      <ul className="mt-1 space-y-1">
                        {message.quality.recommendations.map((rec, i) => (
                          <li key={i} className="text-[var(--text-secondary)]">• {rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          {/* Source Badges */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-[var(--border)]">
              <div className="flex items-center gap-3">
                <button
                  onClick={handleSourceClick}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs
                             bg-[var(--bg-elevated)] text-[var(--text-secondary)]
                             hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)]
                             transition-colors"
                >
                  <FileText size={14} />
                  {message.sources.length} sources
                </button>
                
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="flex items-center gap-1 text-xs text-[var(--text-muted)]
                             hover:text-[var(--text-primary)] transition-colors"
                >
                  {showSources ? (
                    <>
                      <ChevronUp size={14} /> Hide
                    </>
                  ) : (
                    <>
                      <ChevronDown size={14} /> Show
                    </>
                  )}
                </button>
              </div>
              
              {showSources && (
                <div className="mt-3 grid gap-2">
                  {message.sources.slice(0, 3).map((source, idx) => (
                    <SourceRow key={source.id} source={source} index={idx + 1} />
                  ))}
                  {message.sources.length > 3 && (
                    <div className="text-xs text-[var(--text-muted)] pl-8">
                      +{message.sources.length - 3} more sources
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SourceRow({ source, index }: { source: Source; index: number }) {
  const getIcon = () => {
    switch (source.source) {
      case 'ksei_pdf':
        return <FileText size={14} className="text-[var(--accent-gold)]" />;
      case 'ksei_json':
        return <Database size={14} className="text-[var(--accent-green)]" />;
      default:
        return <Database size={14} className="text-[var(--text-muted)]" />;
    }
  };

  const getLabel = () => {
    if (source.source === 'ksei_pdf') {
      return `${source.filename}, Page ${source.page_number}`;
    }
    if (source.source === 'ksei_json') {
      return `${source.ticker} - ${source.date}`;
    }
    return 'Unknown source';
  };

  return (
    <div className="flex items-start gap-2 text-sm">
      <div className="mt-0.5">{getIcon()}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[var(--text-secondary)]">{getLabel()}</span>
          <span className="text-xs text-[var(--accent)]">
            {Math.round((1 - source.distance) * 100)}%
          </span>
        </div>
        <p className="text-xs text-[var(--text-muted)] truncate">
          {source.text_preview?.slice(0, 100)}...
        </p>
      </div>
    </div>
  );
}
