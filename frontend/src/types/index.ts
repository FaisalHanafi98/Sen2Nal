export interface StockSentiment {
  ticker: string
  companyName: string
  sector: string
  marketCap: number
  sp500Rank: number
  nlpScore: number
  calendarScore: number
  combinedScore: number
  signal: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'AVOID'
  confidence: number
  conflictFlag: boolean
  newsCount: number
  redditCount: number
  change24h: number
}

export interface SentimentHistory {
  date: string
  nlpScore: number
  calendarScore: number
  combinedScore: number
  newsCount: number
}

export interface ExperimentStock {
  ticker: string
  entryPrice: number
  exitPrice: number
  return: number
}

export interface ExperimentWeek {
  weekNumber: number
  method: 'SEN2NAL' | 'CHATGPT' | 'GEMINI' | 'GROK'
  stocks: ExperimentStock[]
  weeklyReturn: number
  isWinner: boolean
}

export interface FearGreed {
  score: number
  classification: string
  prevScore: number
  change: number
}

export interface PipelineLog {
  timestamp: string
  stage: string
  message: string
  level: 'info' | 'warning' | 'error' | 'success'
}

export interface PipelineStatus {
  stage: string
  status: 'idle' | 'running' | 'complete' | 'error'
  outcome?: 'unreported' | 'success' | 'failed' | 'invalid' | 'partial'
  lastRun: string
  duration: number
}

export type PipelineRunStatus = 'idle' | 'running' | 'success' | 'failed' | 'unverified'

export interface DashboardData {
  dataMode: 'live' | 'sample'
  pipelineRunStatus: PipelineRunStatus
  stocks: StockSentiment[]
  sentimentHistory: SentimentHistory[]
  experiments: ExperimentWeek[]
  fearGreed: FearGreed
  pipelineLogs: PipelineLog[]
  pipelineStatuses: PipelineStatus[]
}
