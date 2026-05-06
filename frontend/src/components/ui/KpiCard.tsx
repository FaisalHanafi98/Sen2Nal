import { motion } from 'framer-motion'
import { staggerItem } from '@/lib/animations'
import { cn } from '@/lib/utils'

interface Props {
  label: string
  value: string
  subtitle?: string
  trend?: { value: number; label: string }
  glowColor?: 'cyan' | 'purple' | 'bullish' | 'bearish' | 'warning'
}

const glowMap = {
  cyan: 'glow-cyan',
  purple: 'glow-purple',
  bullish: 'glow-bullish',
  bearish: 'glow-bearish',
  warning: '',
}

export default function KpiCard({ label, value, subtitle, trend, glowColor = 'cyan' }: Props) {
  return (
    <motion.div
      variants={staggerItem}
      className={cn(
        'bg-nightops-card border border-nightops-border rounded-lg p-4',
        glowMap[glowColor]
      )}
    >
      <p className="text-xs text-nightops-muted uppercase tracking-wider font-body">{label}</p>
      <p className="text-2xl font-header font-bold mt-1 text-nightops-text">{value}</p>
      {subtitle && (
        <p className="text-xs text-nightops-secondary mt-1">{subtitle}</p>
      )}
      {trend && (
        <div className="flex items-center gap-1 mt-2">
          <span
            className={cn(
              'text-xs font-mono',
              trend.value >= 0 ? 'text-nightops-bullish' : 'text-nightops-bearish'
            )}
          >
            {trend.value >= 0 ? '+' : ''}{trend.value.toFixed(1)}%
          </span>
          <span className="text-xs text-nightops-muted">{trend.label}</span>
        </div>
      )}
    </motion.div>
  )
}
