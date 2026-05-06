import { cn, signalColor, formatScore, formatMarketCap } from '@/lib/utils'
import { SIGNAL_LABELS } from '@/lib/constants'
import type { StockSentiment } from '@/types'

interface Props {
  stocks: StockSentiment[]
}

export default function DataTable({ stocks }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-nightops-border text-nightops-muted text-left">
            <th className="py-2 px-3">#</th>
            <th className="py-2 px-3">Ticker</th>
            <th className="py-2 px-3">Sector</th>
            <th className="py-2 px-3 text-right">Mkt Cap</th>
            <th className="py-2 px-3 text-right">NLP</th>
            <th className="py-2 px-3 text-right">Calendar</th>
            <th className="py-2 px-3 text-right">Combined</th>
            <th className="py-2 px-3 text-center">Signal</th>
            <th className="py-2 px-3 text-right">24h</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((s) => (
            <tr
              key={s.ticker}
              className="border-b border-nightops-border/50 hover:bg-nightops-elevated/50 transition-colors"
            >
              <td className="py-2 px-3 text-nightops-muted">{s.sp500Rank}</td>
              <td className="py-2 px-3 font-bold text-nightops-text">{s.ticker}</td>
              <td className="py-2 px-3 text-nightops-secondary">{s.sector}</td>
              <td className="py-2 px-3 text-right text-nightops-secondary">{formatMarketCap(s.marketCap)}</td>
              <td className="py-2 px-3 text-right">{formatScore(s.nlpScore)}</td>
              <td className="py-2 px-3 text-right">{formatScore(s.calendarScore)}</td>
              <td className="py-2 px-3 text-right text-nightops-cyan font-bold">{formatScore(s.combinedScore)}</td>
              <td className={cn('py-2 px-3 text-center font-bold', signalColor(s.signal))}>
                {SIGNAL_LABELS[s.signal] ?? s.signal}
              </td>
              <td className={cn('py-2 px-3 text-right', s.change24h >= 0 ? 'text-nightops-bullish' : 'text-nightops-bearish')}>
                {s.change24h >= 0 ? '+' : ''}{(s.change24h * 100).toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
