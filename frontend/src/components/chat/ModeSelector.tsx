import { useState, useEffect } from 'react';
import { Shield, Scale, Sparkles } from 'lucide-react';
import { getModes } from '@/lib/api';
import { cn } from '@/lib/utils';
import type { ResponseMode } from '@/types';

interface ModeSelectorProps {
  value: string;
  onChange: (mode: string) => void;
  className?: string;
}

const modeIcons: Record<string, React.ElementType> = {
  strict: Shield,
  balanced: Scale,
  explorative: Sparkles,
};

const modeColors: Record<string, string> = {
  strict: 'text-green-400',
  balanced: 'text-blue-400',
  explorative: 'text-purple-400',
};

export function ModeSelector({ value, onChange, className }: ModeSelectorProps) {
  const [modes, setModes] = useState<Record<string, ResponseMode>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getModes().then((data) => {
      setModes(data);
      setLoading(false);
    }).catch(() => {
      // Fallback modes
      setModes({
        strict: {
          description: 'Only use retrieved data, no assumptions',
          temperature: 0.1,
          creativity: 0,
          allow_inference: false,
          allow_general_knowledge: false,
        },
        balanced: {
          description: 'Use data + reasonable connections',
          temperature: 0.3,
          creativity: 0.3,
          allow_inference: true,
          allow_general_knowledge: false,
        },
        explorative: {
          description: 'Broader analysis with clear uncertainty markers',
          temperature: 0.5,
          creativity: 0.6,
          allow_inference: true,
          allow_general_knowledge: true,
        },
      });
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className={cn('flex gap-2', className)}>
        <div className="h-8 w-24 bg-[var(--bg-elevated)] rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {Object.entries(modes).map(([modeKey, modeConfig]) => {
        const Icon = modeIcons[modeKey] || Scale;
        const isActive = value === modeKey;
        
        return (
          <button
            key={modeKey}
            onClick={() => onChange(modeKey)}
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
              isActive
                ? `bg-[var(--bg-elevated)] border border-[var(--border)] ${modeColors[modeKey]}`
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)]'
            )}
            title={modeConfig.description}
          >
            <Icon size={14} />
            <span className="capitalize">{modeKey}</span>
          </button>
        );
      })}
    </div>
  );
}

interface QualityBadgeProps {
  quality?: {
    quality_score: number;
    coverage: string;
  };
  className?: string;
}

export function QualityBadge({ quality, className }: QualityBadgeProps) {
  if (!quality) return null;
  
  const score = quality.quality_score;
  let color = 'text-red-400';
  let label = 'Low';
  
  if (score >= 80) {
    color = 'text-green-400';
    label = 'High';
  } else if (score >= 50) {
    color = 'text-yellow-400';
    label = 'Medium';
  }
  
  return (
    <div className={cn('flex items-center gap-2 text-xs', className)}>
      <span className="text-[var(--text-muted)]">Data Quality:</span>
      <span className={cn('font-medium', color)}>
        {label} ({score}%)
      </span>
      <span className="text-[var(--text-muted)]">
        Coverage: <span className="capitalize">{quality.coverage}</span>
      </span>
    </div>
  );
}
