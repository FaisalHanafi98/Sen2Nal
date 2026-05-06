import { useQuery } from '@tanstack/react-query'
import type { DashboardData, StockSentiment, SentimentHistory, ExperimentWeek, FearGreed, PipelineLog, PipelineStatus } from '@/types'
import apiClient from './client'
import { fetchDashboardData as fetchMockData } from './mock/handlers'

const USE_MOCK = import.meta.env.VITE_USE_MOCK_DATA !== 'false'

async function fetchLiveData(): Promise<DashboardData> {
  const [stocksRes, historyRes, expRes, fgRes, pipeRes, logsRes] = await Promise.all([
    apiClient.get('/stocks'),
    apiClient.get('/stocks/history', { params: { ticker: 'AAPL', days: 30 } }),
    apiClient.get('/experiments'),
    apiClient.get('/stocks/fear-greed'),
    apiClient.get('/pipeline/status'),
    apiClient.get('/pipeline/logs'),
  ])

  return {
    stocks: stocksRes.data.stocks ?? [],
    sentimentHistory: historyRes.data.history ?? [],
    experiments: expRes.data.experiments ?? [],
    fearGreed: fgRes.data ?? { score: 50, classification: 'Neutral', prevScore: 50, change: 0 },
    pipelineLogs: logsRes.data.logs ?? [],
    pipelineStatuses: pipeRes.data.stages ?? [],
  }
}

export function useDashboardData() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: USE_MOCK ? fetchMockData : fetchLiveData,
    refetchInterval: 60_000,
  })
}

export function useStocks(limit = 10, sector?: string) {
  return useQuery({
    queryKey: ['stocks', limit, sector],
    queryFn: async () => {
      if (USE_MOCK) return (await fetchMockData()).stocks
      const { data } = await apiClient.get('/stocks', { params: { limit, sector } })
      return data.stocks as StockSentiment[]
    },
    refetchInterval: 60_000,
  })
}

export function useSentimentHistory(ticker: string, days = 30) {
  return useQuery({
    queryKey: ['history', ticker, days],
    queryFn: async () => {
      if (USE_MOCK) return (await fetchMockData()).sentimentHistory
      const { data } = await apiClient.get('/stocks/history', { params: { ticker, days } })
      return data.history as SentimentHistory[]
    },
    refetchInterval: 120_000,
  })
}

export function useExperiments() {
  return useQuery({
    queryKey: ['experiments'],
    queryFn: async () => {
      if (USE_MOCK) return (await fetchMockData()).experiments
      const { data } = await apiClient.get('/experiments')
      return data.experiments as ExperimentWeek[]
    },
    refetchInterval: 300_000,
  })
}

export function useFearGreed() {
  return useQuery({
    queryKey: ['fear-greed'],
    queryFn: async () => {
      if (USE_MOCK) return (await fetchMockData()).fearGreed
      const { data } = await apiClient.get('/stocks/fear-greed')
      return data as FearGreed
    },
    refetchInterval: 300_000,
  })
}

export function usePipelineStatus() {
  return useQuery({
    queryKey: ['pipeline-status'],
    queryFn: async () => {
      if (USE_MOCK) return (await fetchMockData()).pipelineStatuses
      const { data } = await apiClient.get('/pipeline/status')
      return data.stages as PipelineStatus[]
    },
    refetchInterval: 30_000,
  })
}

export function usePipelineLogs() {
  return useQuery({
    queryKey: ['pipeline-logs'],
    queryFn: async () => {
      if (USE_MOCK) return (await fetchMockData()).pipelineLogs
      const { data } = await apiClient.get('/pipeline/logs')
      return data.logs as PipelineLog[]
    },
    refetchInterval: 15_000,
  })
}
