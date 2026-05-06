import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { COLORS, CHART_THEME } from '@/lib/constants'
import type { SentimentHistory } from '@/types'

interface Props {
  data: SentimentHistory[]
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; name: string; color: string }>; label?: string }) {
  if (!active || !payload) return null
  return (
    <div className="bg-nightops-elevated border border-nightops-border rounded-lg p-3 text-xs font-mono">
      <p className="text-nightops-secondary mb-2">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(3) : p.value}
        </p>
      ))}
    </div>
  )
}

export default function SentimentTimeline({ data }: Props) {
  return (
    <div className="bg-nightops-card border border-nightops-border rounded-lg p-4">
      <h3 className="text-sm font-header font-semibold text-nightops-text mb-4">
        Sentiment Timeline (30d)
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="gradCyan" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS.cyan} stopOpacity={0.3} />
              <stop offset="95%" stopColor={COLORS.cyan} stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradPurple" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS.purple} stopOpacity={0.3} />
              <stop offset="95%" stopColor={COLORS.purple} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_THEME.grid} />
          <XAxis
            dataKey="date"
            stroke={CHART_THEME.axis}
            tick={{ fontSize: 10, fill: CHART_THEME.axis }}
            tickFormatter={(v: string) => v.slice(5)}
          />
          <YAxis
            stroke={CHART_THEME.axis}
            tick={{ fontSize: 10, fill: CHART_THEME.axis }}
            domain={[0, 1]}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="line"
            wrapperStyle={{ fontSize: 10, fontFamily: 'JetBrains Mono' }}
          />
          <Area
            type="monotone"
            dataKey="combinedScore"
            name="Combined"
            stroke={COLORS.cyan}
            fill="url(#gradCyan)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="nlpScore"
            name="NLP"
            stroke={COLORS.purple}
            fill="url(#gradPurple)"
            strokeWidth={1.5}
          />
          <Area
            type="monotone"
            dataKey="calendarScore"
            name="Calendar"
            stroke={COLORS.bullish}
            fill="transparent"
            strokeWidth={1}
            strokeDasharray="4 4"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
