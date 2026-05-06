import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface Props {
  children: ReactNode
  color?: 'cyan' | 'purple' | 'bullish'
  className?: string
}

const glowMap = {
  cyan: 'glow-cyan',
  purple: 'glow-purple',
  bullish: 'glow-bullish',
}

export default function GlowBorder({ children, color = 'cyan', className }: Props) {
  return (
    <div className={cn('bg-nightops-card border border-nightops-border rounded-lg', glowMap[color], className)}>
      {children}
    </div>
  )
}
