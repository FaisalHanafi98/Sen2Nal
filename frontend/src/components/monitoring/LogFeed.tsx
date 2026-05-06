import { useRef, useEffect } from 'react'
import { cn, formatTimestamp } from '@/lib/utils'
import type { PipelineLog } from '@/types'

interface Props {
  logs: PipelineLog[]
}

const levelColors = {
  info: 'text-nightops-secondary',
  warning: 'text-nightops-warning',
  error: 'text-nightops-bearish',
  success: 'text-nightops-bullish',
}

const levelIcons = {
  info: '>>',
  warning: '!!',
  error: 'XX',
  success: 'OK',
}

export default function LogFeed({ logs }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs])

  return (
    <div className="bg-nightops-card border border-nightops-border rounded-lg p-4">
      <h3 className="text-sm font-header font-semibold text-nightops-text mb-3">
        Pipeline Log
      </h3>
      <div
        ref={scrollRef}
        className="h-48 overflow-y-auto font-mono text-[11px] leading-relaxed space-y-0.5"
      >
        {logs.map((log, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-nightops-muted shrink-0">{formatTimestamp(log.timestamp)}</span>
            <span className={cn('shrink-0 w-5', levelColors[log.level])}>{levelIcons[log.level]}</span>
            <span className="text-nightops-cyan shrink-0 w-20 truncate">[{log.stage}]</span>
            <span className={cn(levelColors[log.level])}>{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
