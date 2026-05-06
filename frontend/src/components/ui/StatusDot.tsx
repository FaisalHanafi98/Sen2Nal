import { cn } from '@/lib/utils'

interface Props {
  status: 'online' | 'warning' | 'offline'
  size?: 'sm' | 'md'
}

const statusColors = {
  online: 'bg-nightops-bullish',
  warning: 'bg-nightops-warning',
  offline: 'bg-nightops-bearish',
}

export default function StatusDot({ status, size = 'sm' }: Props) {
  return (
    <span
      className={cn(
        'rounded-full animate-pulse-dot inline-block',
        statusColors[status],
        size === 'sm' ? 'w-1.5 h-1.5' : 'w-2.5 h-2.5'
      )}
    />
  )
}
