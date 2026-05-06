import { motion } from 'framer-motion'
import { staggerContainer, staggerItem } from '@/lib/animations'
import { useDashboardData } from '@/api/hooks'
import KpiCard from '@/components/ui/KpiCard'
import DataTable from '@/components/ui/DataTable'
import SentimentTimeline from '@/components/monitoring/SentimentTimeline'
import SentimentGauge from '@/components/monitoring/SentimentGauge'
import SentimentTreemap from '@/components/monitoring/SentimentTreemap'
import LogFeed from '@/components/monitoring/LogFeed'
import ExperimentTable from '@/components/experiments/ExperimentTable'
import AiVsHumanPanel from '@/components/experiments/AiVsHumanPanel'
import PipelineFlow from '@/components/pipeline/PipelineFlow'

export default function Dashboard() {
  const { data, isLoading } = useDashboardData()

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-nightops-cyan font-mono text-sm animate-pulse">
          Loading NightOps Terminal...
        </div>
      </div>
    )
  }

  const bullishCount = data.stocks.filter((s) => s.signal === 'STRONG_BUY' || s.signal === 'BUY').length
  const bullishPct = ((bullishCount / data.stocks.length) * 100).toFixed(0)
  const pipelineRunning = data.pipelineStatuses.some((s) => s.status === 'running')

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* KPI Row */}
      <motion.div variants={staggerContainer} className="grid grid-cols-4 gap-4">
        <KpiCard
          label="Active Signals"
          value={`${data.stocks.length}`}
          subtitle="S&P 500 top 10"
          trend={{ value: 2.5, label: 'vs last week' }}
          glowColor="cyan"
        />
        <KpiCard
          label="Bullish Ratio"
          value={`${bullishPct}%`}
          subtitle={`${bullishCount} of ${data.stocks.length} stocks`}
          trend={{ value: 5.0, label: 'vs last week' }}
          glowColor="bullish"
        />
        <KpiCard
          label="Pipeline Status"
          value={pipelineRunning ? 'Running' : 'Idle'}
          subtitle="Daily batch @ 06:00 UTC"
          glowColor="purple"
        />
        <KpiCard
          label="Fear & Greed"
          value={`${data.fearGreed.score}`}
          subtitle={data.fearGreed.classification}
          trend={{ value: data.fearGreed.change, label: 'vs yesterday' }}
          glowColor={data.fearGreed.score >= 50 ? 'bullish' : 'bearish'}
        />
      </motion.div>

      {/* Charts Row: Timeline + Gauge */}
      <motion.div variants={staggerItem} className="grid grid-cols-4 gap-4">
        <div className="col-span-3">
          <SentimentTimeline data={data.sentimentHistory} />
        </div>
        <div className="col-span-1">
          <SentimentGauge data={data.fearGreed} />
        </div>
      </motion.div>

      {/* Treemap */}
      <motion.div variants={staggerItem}>
        <SentimentTreemap stocks={data.stocks} />
      </motion.div>

      {/* Pipeline Flow */}
      <motion.div variants={staggerItem}>
        <PipelineFlow statuses={data.pipelineStatuses} />
      </motion.div>

      {/* Data Table */}
      <motion.div variants={staggerItem} className="bg-nightops-card border border-nightops-border rounded-lg p-4">
        <h3 className="text-sm font-header font-semibold text-nightops-text mb-3">
          Top 10 Stocks — Sentiment Scores
        </h3>
        <DataTable stocks={data.stocks} />
      </motion.div>

      {/* Experiments Row */}
      <motion.div variants={staggerItem} className="grid grid-cols-2 gap-4">
        <ExperimentTable experiments={data.experiments} />
        <AiVsHumanPanel experiments={data.experiments} />
      </motion.div>

      {/* Log Feed */}
      <motion.div variants={staggerItem}>
        <LogFeed logs={data.pipelineLogs} />
      </motion.div>

      {/* Disclaimer Footer */}
      <motion.div variants={staggerItem} className="text-center py-4">
        <p className="text-[10px] text-nightops-muted font-mono leading-relaxed max-w-xl mx-auto">
          Sen2Nal is NOT a financial advisor. All signals are for informational and educational purposes only.
          Past performance does not guarantee future results. All investment decisions are your responsibility.
        </p>
      </motion.div>
    </motion.div>
  )
}
