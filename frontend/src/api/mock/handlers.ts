import type { DashboardData } from '@/types'
import {
  mockStocks,
  mockSentimentHistory,
  mockExperiments,
  mockFearGreed,
  mockPipelineLogs,
  mockPipelineStatuses,
} from './data'

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export async function fetchDashboardData(): Promise<DashboardData> {
  await delay(300)
  return {
    stocks: mockStocks,
    sentimentHistory: mockSentimentHistory,
    experiments: mockExperiments,
    fearGreed: mockFearGreed,
    pipelineLogs: mockPipelineLogs,
    pipelineStatuses: mockPipelineStatuses,
  }
}
