import { useMemo } from 'react'
import { cn } from '@/lib/utils'
import type { ExperimentWeek } from '@/types'

interface Props {
  experiments: ExperimentWeek[]
}

interface MethodSummary {
  method: string
  totalReturn: number
  wins: number
  weeks: number
}

export default function ExperimentTable({ experiments }: Props) {
  const weekNumbers = useMemo(
    () => [...new Set(experiments.map((e) => e.weekNumber))].sort((a, b) => a - b),
    [experiments]
  )
  const methods = ['SEN2NAL', 'CHATGPT', 'GEMINI', 'GROK'] as const

  const summaries = useMemo<MethodSummary[]>(() => {
    return methods.map((method) => {
      const rows = experiments.filter((e) => e.method === method)
      return {
        method,
        totalReturn: rows.reduce((sum, r) => sum + r.weeklyReturn, 0),
        wins: rows.filter((r) => r.isWinner).length,
        weeks: rows.length,
      }
    })
  }, [experiments])

  const methodColors: Record<string, string> = {
    SEN2NAL: 'text-nightops-cyan',
    CHATGPT: 'text-nightops-bullish',
    GEMINI: 'text-nightops-purple',
    GROK: 'text-nightops-warning',
  }

  return (
    <div className="bg-nightops-card border border-nightops-border rounded-lg p-4">
      <h3 className="text-sm font-header font-semibold text-nightops-text mb-3">
        LLM Experiment — Weekly Returns
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="border-b border-nightops-border text-nightops-muted text-left">
              <th className="py-2 px-2">Method</th>
              {weekNumbers.map((w) => (
                <th key={w} className="py-2 px-2 text-center">W{w}</th>
              ))}
              <th className="py-2 px-2 text-right">Total</th>
              <th className="py-2 px-2 text-center">Wins</th>
            </tr>
          </thead>
          <tbody>
            {summaries.map((s) => (
              <tr key={s.method} className="border-b border-nightops-border/50">
                <td className={cn('py-2 px-2 font-bold', methodColors[s.method])}>
                  {s.method}
                </td>
                {weekNumbers.map((w) => {
                  const row = experiments.find((e) => e.method === s.method && e.weekNumber === w)
                  if (!row) return <td key={w} className="py-2 px-2 text-center text-nightops-muted">-</td>
                  return (
                    <td
                      key={w}
                      className={cn(
                        'py-2 px-2 text-center',
                        row.weeklyReturn >= 0 ? 'text-nightops-bullish' : 'text-nightops-bearish',
                        row.isWinner && 'font-bold underline'
                      )}
                    >
                      {row.weeklyReturn >= 0 ? '+' : ''}{(row.weeklyReturn * 100).toFixed(1)}%
                    </td>
                  )
                })}
                <td className={cn(
                  'py-2 px-2 text-right font-bold',
                  s.totalReturn >= 0 ? 'text-nightops-bullish' : 'text-nightops-bearish'
                )}>
                  {s.totalReturn >= 0 ? '+' : ''}{(s.totalReturn * 100).toFixed(1)}%
                </td>
                <td className="py-2 px-2 text-center text-nightops-cyan">{s.wins}/{s.weeks}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
