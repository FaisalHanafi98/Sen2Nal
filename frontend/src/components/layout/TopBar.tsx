import { useSystemClock } from '@/hooks/useSystemClock'
import StatusDot from '@/components/ui/StatusDot'

export default function TopBar() {
  const { utc, date } = useSystemClock()

  return (
    <header className="h-12 border-b border-nightops-border bg-nightops-card flex items-center justify-between px-6">
      {/* Branding */}
      <div className="flex items-center gap-3">
        <span className="font-header text-lg font-bold tracking-wider text-nightops-cyan">
          SEN2NAL
        </span>
        <span className="text-xs text-nightops-muted font-mono">NightOps Terminal</span>
      </div>

      {/* System Status */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <StatusDot status="online" />
            <span className="text-nightops-secondary">Pipeline</span>
          </div>
          <div className="flex items-center gap-1.5">
            <StatusDot status="online" />
            <span className="text-nightops-secondary">Database</span>
          </div>
          <div className="flex items-center gap-1.5">
            <StatusDot status="warning" />
            <span className="text-nightops-secondary">API</span>
          </div>
        </div>

        {/* Clock */}
        <div className="flex items-center gap-2 text-xs font-mono text-nightops-muted border-l border-nightops-border pl-4">
          <span>{date}</span>
          <span className="text-nightops-cyan">{utc}</span>
          <span className="text-nightops-muted">UTC</span>
        </div>
      </div>
    </header>
  )
}
