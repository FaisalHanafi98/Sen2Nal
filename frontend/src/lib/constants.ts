export const COLORS = {
  bg: '#0A0E17',
  card: '#111827',
  elevated: '#1A1F2E',
  cyan: '#06B6D4',
  purple: '#8B5CF6',
  bullish: '#10B981',
  warning: '#F59E0B',
  bearish: '#EF4444',
  text: '#F1F5F9',
  secondary: '#94A3B8',
  muted: '#64748B',
  border: '#1E293B',
} as const

export const SIGNAL_COLORS: Record<string, string> = {
  STRONG_BUY: COLORS.bullish,
  BUY: '#34D399',
  HOLD: COLORS.warning,
  AVOID: COLORS.bearish,
}

export const SIGNAL_LABELS: Record<string, string> = {
  STRONG_BUY: 'Strong Buy',
  BUY: 'Buy',
  HOLD: 'Hold',
  AVOID: 'Avoid',
}

export const PIPELINE_STAGES = [
  'Data Ingestion',
  'FinBERT NLP',
  'Feature Engineering',
  'XGBoost Prediction',
  'Output & Storage',
] as const

export const CHART_THEME = {
  grid: COLORS.border,
  axis: COLORS.muted,
  tooltip: {
    bg: COLORS.elevated,
    border: COLORS.border,
    text: COLORS.text,
  },
} as const
