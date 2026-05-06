import type { FearGreed } from '@/types'
import { cn } from '@/lib/utils'

interface Props {
  data: FearGreed
}

export default function SentimentGauge({ data }: Props) {
  const { score, classification, change } = data
  const radius = 70
  const centerX = 90
  const centerY = 85

  // Arc path for the gauge background
  const arcPath = `M ${centerX - radius} ${centerY} A ${radius} ${radius} 0 0 1 ${centerX + radius} ${centerY}`

  // Needle endpoint
  const needleAngle = ((score / 100) * Math.PI)
  const needleX = centerX - Math.cos(needleAngle) * (radius - 8)
  const needleY = centerY - Math.sin(needleAngle) * (radius - 8)

  const scoreColor =
    score >= 75 ? 'text-nightops-bullish' :
    score >= 50 ? 'text-nightops-cyan' :
    score >= 25 ? 'text-nightops-warning' :
    'text-nightops-bearish'

  return (
    <div className="bg-nightops-card border border-nightops-border rounded-lg p-4 flex flex-col items-center">
      <h3 className="text-sm font-header font-semibold text-nightops-text mb-2">
        Fear & Greed Index
      </h3>

      <svg width="180" height="110" viewBox="0 0 180 110">
        {/* Background arc */}
        <defs>
          <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#EF4444" />
            <stop offset="25%" stopColor="#F59E0B" />
            <stop offset="50%" stopColor="#06B6D4" />
            <stop offset="75%" stopColor="#10B981" />
            <stop offset="100%" stopColor="#10B981" />
          </linearGradient>
        </defs>
        <path d={arcPath} fill="none" stroke="url(#gaugeGrad)" strokeWidth="12" strokeLinecap="round" />

        {/* Needle */}
        <line
          x1={centerX}
          y1={centerY}
          x2={needleX}
          y2={needleY}
          stroke="#F1F5F9"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <circle cx={centerX} cy={centerY} r="4" fill="#F1F5F9" />

        {/* Labels */}
        <text x="12" y="100" fill="#64748B" fontSize="8" fontFamily="JetBrains Mono">Fear</text>
        <text x="148" y="100" fill="#64748B" fontSize="8" fontFamily="JetBrains Mono">Greed</text>
      </svg>

      <div className="text-center mt-1">
        <span className={cn('text-3xl font-header font-bold', scoreColor)}>{score}</span>
        <p className="text-xs text-nightops-secondary mt-0.5">{classification}</p>
        <p className={cn(
          'text-xs font-mono mt-1',
          change >= 0 ? 'text-nightops-bullish' : 'text-nightops-bearish'
        )}>
          {change >= 0 ? '+' : ''}{change} from yesterday
        </p>
      </div>
    </div>
  )
}
