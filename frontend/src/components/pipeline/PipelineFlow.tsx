import { motion } from 'framer-motion'
import { COLORS } from '@/lib/constants'
import type { PipelineStatus } from '@/types'

interface Props {
  statuses: PipelineStatus[]
}

const statusColors = {
  idle: COLORS.muted,
  running: COLORS.cyan,
  complete: COLORS.bullish,
  error: COLORS.bearish,
}

const pipelineStages = [
  { stage: 'Data Ingestion', icon: 'IN' },
  { stage: 'FinBERT NLP', icon: 'NLP' },
  { stage: 'Calendar Patterns', icon: 'CAL' },
  { stage: 'Feature Engineering', icon: 'FE' },
  { stage: 'XGBoost Prediction', icon: 'ML' },
  { stage: 'Output & Storage', icon: 'OUT' },
]
const stageStatusLabels = {
  idle: 'Unreported',
  running: 'Running',
  complete: 'Complete',
  error: 'Error',
}

export default function PipelineFlow({ statuses }: Props) {
  return (
    <div className="bg-nightops-card border border-nightops-border rounded-lg p-4">
      <h3 className="text-sm font-header font-semibold text-nightops-text mb-4">
        ML Pipeline Status
      </h3>

      <div className="flex items-center justify-between overflow-x-auto px-2">
        {pipelineStages.map(({ stage, icon }, i) => {
          const status = statuses.find((s) => s.stage === stage)
          const state = status?.status ?? 'idle'
          const color = statusColors[state]
          const isRunning = status?.status === 'running'

          return (
            <div key={stage} className="flex shrink-0 items-center">
              {/* Node */}
              <div className="flex flex-col items-center gap-2">
                <motion.div
                  animate={isRunning ? {
                    boxShadow: [
                      `0 0 0px ${color}`,
                      `0 0 20px ${color}`,
                      `0 0 0px ${color}`,
                    ],
                  } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="w-12 h-12 rounded-lg border-2 flex items-center justify-center"
                  style={{ borderColor: color, backgroundColor: `${color}15` }}
                >
                  <span className="text-xs font-mono font-bold" style={{ color }}>
                    {icon}
                  </span>
                </motion.div>
                <div className="text-center">
                  <p className="text-[10px] font-mono text-nightops-secondary leading-tight max-w-16">
                    {stage}
                  </p>
                  <p className="text-[9px] font-mono mt-0.5" style={{ color }}>
                    {stageStatusLabels[state]}
                    {status && state !== 'idle' && stage !== 'Output & Storage'
                      ? ` · ${status.duration.toFixed(1)}s` : ''}
                  </p>
                </div>
              </div>

              {/* Connector */}
              {i < pipelineStages.length - 1 && (
                <svg width="40" height="4" className="mx-1 -mt-6">
                  <motion.line
                    x1="0" y1="2" x2="40" y2="2"
                    stroke={color}
                    strokeWidth="2"
                    strokeDasharray="6 4"
                    animate={{ strokeDashoffset: [20, 0] }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                </svg>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
