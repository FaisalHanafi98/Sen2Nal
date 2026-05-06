import { cn } from '@/lib/utils'

interface NavItem {
  label: string
  icon: string
  active?: boolean
}

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: '/', active: true },
  { label: 'Stocks', icon: '$' },
  { label: 'Experiments', icon: '~' },
  { label: 'Pipeline', icon: '>' },
]

export default function Sidebar() {
  return (
    <aside className="w-48 border-r border-nightops-border bg-nightops-card flex flex-col">
      {/* Navigation */}
      <nav className="flex-1 py-4">
        {navItems.map((item) => (
          <button
            key={item.label}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors',
              item.active
                ? 'text-nightops-cyan bg-nightops-cyan/10 border-r-2 border-nightops-cyan'
                : 'text-nightops-secondary hover:text-nightops-text hover:bg-nightops-elevated'
            )}
          >
            <span className="font-mono text-xs w-4 text-center opacity-60">{item.icon}</span>
            <span className="font-body">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-nightops-border">
        <div className="text-[10px] text-nightops-muted font-mono leading-relaxed">
          <p>Sen2Nal v1.0.0</p>
          <p>NOT FINANCIAL ADVICE</p>
        </div>
      </div>
    </aside>
  )
}
