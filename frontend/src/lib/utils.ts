import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatNumber(value: number, decimals = 2): string {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function formatPercent(value: number, decimals = 1): string {
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(decimals)}%`
}

export function formatScore(value: number): string {
  return value.toFixed(3)
}

export function formatMarketCap(value: number): string {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`
  return `$${value.toLocaleString()}`
}

export function formatTimestamp(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function signalColor(signal: string): string {
  const map: Record<string, string> = {
    STRONG_BUY: 'text-nightops-bullish',
    BUY: 'text-emerald-400',
    HOLD: 'text-nightops-warning',
    AVOID: 'text-nightops-bearish',
  }
  return map[signal] ?? 'text-nightops-secondary'
}
