import { useEffect, useRef, useState } from 'react';
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  ColorType,
  CrosshairMode,
} from 'lightweight-charts';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface OhlcvBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  value: number;
  net_foreign: number;
}

interface CandlestickChartProps {
  ticker: string;
  data: OhlcvBar[];
  className?: string;
}

function formatPrice(v: number | null | undefined) {
  if (v == null) return 'N/A';
  return `Rp ${v.toLocaleString('id-ID')}`;
}

function formatVol(v: number | null | undefined) {
  if (v == null) return 'N/A';
  if (v >= 1e12) return `${(v / 1e12).toFixed(1)}T`;
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  return v.toLocaleString();
}

export function CandlestickChart({ ticker, data, className = '' }: CandlestickChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState<OhlcvBar | null>(null);

  const last = data[data.length - 1];
  const prev = data[data.length - 2];
  const change = last && prev ? ((last.close - prev.close) / prev.close) * 100 : null;
  const isUp = change != null ? change >= 0 : null;

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    const chart = createChart(chartRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.05)' },
        horzLines: { color: 'rgba(255,255,255,0.05)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#3b82f6', style: 1, width: 1 },
        horzLine: { color: '#3b82f6', style: 1, width: 1 },
      },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)' },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.1)',
        timeVisible: true,
        secondsVisible: false,
      },
      width: chartRef.current.clientWidth,
      height: 240,
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    const volSeries = chart.addSeries(HistogramSeries, {
      color: '#3b82f620',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    const foreignSeries = chart.addSeries(LineSeries, {
      color: '#f59e0b',
      lineWidth: 1,
      priceScaleId: 'foreign',
      title: 'Asing Net',
    });

    chart.priceScale('foreign').applyOptions({
      scaleMargins: { top: 0.7, bottom: 0.05 },
    });

    const candles = data.map(d => ({
      time: d.date as any,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));
    candleSeries.setData(candles);

    const vols = data.map(d => ({
      time: d.date as any,
      value: d.volume || 0,
      color: d.close >= d.open ? '#22c55e30' : '#ef444430',
    }));
    volSeries.setData(vols);

    const foreignData = data
      .filter(d => d.net_foreign != null)
      .map(d => ({ time: d.date as any, value: d.net_foreign }));
    if (foreignData.length > 0) foreignSeries.setData(foreignData);

    chart.subscribeCrosshairMove(param => {
      if (!param.time) { setHovered(null); return; }
      const found = data.find(d => d.date === param.time);
      if (found) setHovered(found);
    });

    chart.timeScale().fitContent();

    const ro = new ResizeObserver(() => {
      if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth });
    });
    if (chartRef.current) ro.observe(chartRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [data]);

  return (
    <div className={`rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-3 py-2 flex items-center justify-between border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-[var(--text-primary)]">{ticker}</span>
          {last && (
            <span className="text-sm text-[var(--text-primary)]">{formatPrice(last.close)}</span>
          )}
          {change != null && (
            <span className={`flex items-center gap-0.5 text-xs font-medium ${isUp ? 'text-green-400' : 'text-red-400'}`}>
              {isUp ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
              {isUp ? '+' : ''}{change.toFixed(2)}%
            </span>
          )}
        </div>
        {hovered && (
          <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
            <span>{hovered.date}</span>
            <span>O: {formatPrice(hovered.open)}</span>
            <span>H: {formatPrice(hovered.high)}</span>
            <span>L: {formatPrice(hovered.low)}</span>
            <span>C: {formatPrice(hovered.close)}</span>
            <span>Vol: {formatVol(hovered.volume)}</span>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="px-3 pt-1 flex gap-3 text-xs text-[var(--text-muted)]">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-green-400 inline-block" />Naik</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-red-400 inline-block" />Turun</span>
        <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-yellow-400 inline-block" />Asing Net</span>
      </div>

      <div ref={chartRef} className="w-full" />

      {/* Footer stats */}
      {last && (
        <div className="px-3 py-1.5 border-t border-[var(--border)] flex gap-4 text-xs text-[var(--text-muted)]">
          <span>Vol: {formatVol(last.volume)}</span>
          <span>Value: {formatVol(last.value)}</span>
          {last.net_foreign != null && (
            <span className={last.net_foreign >= 0 ? 'text-green-400' : 'text-red-400'}>
              Asing: {last.net_foreign >= 0 ? '+' : ''}{formatVol(last.net_foreign)}
            </span>
          )}
          <span className="ml-auto">{data.length} bars</span>
        </div>
      )}
    </div>
  );
}
