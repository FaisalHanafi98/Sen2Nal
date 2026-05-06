import { useMemo } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { COLORS, CHART_THEME } from '@/lib/constants'
import type { ExperimentWeek } from '@/types'

interface Props {
  experiments: ExperimentWeek[]
}

export default function AiVsHumanPanel({ experiments }: Props) {
  const cumulativeData = useMemo(() => {
    const methods = ['SEN2NAL', 'CHATGPT', 'GEMINI', 'GROK'] as const
    const weekNums = [...new Set(experiments.map((e) => e.weekNumber))].sort((a, b) => a - b)

    const cumulative: Record<string, number> = {}
    methods.forEach((m) => (cumulative[m] = 0))

    return weekNums.map((w) => {
      const point: Record<string, number | string> = { week: `W${w}` }
      methods.forEach((m) => {
        const row = experiments.find((e) => e.method === m && e.weekNumber === w)
        cumulative[m] += row ? row.weeklyReturn : 0
        point[m] = +(cumulative[m] * 100).toFixed(2)
      })
      return point
    })
  }, [experiments])

  const methodColors = {
    SEN2NAL: COLORS.cyan,
    CHATGPT: COLORS.bullish,
    GEMINI: COLORS.purple,
    GROK: COLORS.warning,
  }

  return (
    <div className="bg-nightops-card border border-nightops-border rounded-lg p-4">
      <h3 className="text-sm font-header font-semibold text-nightops-text mb-4">
        Cumulative Returns — AI vs AI
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={cumulativeData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_THEME.grid} />
          <XAxis dataKey="week" stroke={CHART_THEME.axis} tick={{ fontSize: 10, fill: CHART_THEME.axis }} />
          <YAxis stroke={CHART_THEME.axis} tick={{ fontSize: 10, fill: CHART_THEME.axis }} tickFormatter={(v: number) => `${v}%`} />
          <Tooltip
            contentStyle={{
              backgroundColor: CHART_THEME.tooltip.bg,
              border: `1px solid ${CHART_THEME.tooltip.border}`,
              borderRadius: 8,
              fontSize: 11,
              fontFamily: 'JetBrains Mono',
            }}
            formatter={(value) => [`${Number(value).toFixed(2)}%`]}
          />
          <Legend iconType="line" wrapperStyle={{ fontSize: 10, fontFamily: 'JetBrains Mono' }} />
          {(Object.entries(methodColors) as [string, string][]).map(([method, color]) => (
            <Area
              key={method}
              type="monotone"
              dataKey={method}
              stroke={color}
              fill="transparent"
              strokeWidth={method === 'SEN2NAL' ? 2.5 : 1.5}
              strokeDasharray={method === 'SEN2NAL' ? undefined : '4 4'}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
