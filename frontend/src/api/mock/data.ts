import type {
  StockSentiment,
  SentimentHistory,
  ExperimentWeek,
  FearGreed,
  PipelineLog,
  PipelineStatus,
} from '@/types'

export const mockStocks: StockSentiment[] = [
  { ticker: 'AAPL', companyName: 'Apple Inc.', sector: 'Technology', marketCap: 3.45e12, sp500Rank: 1, nlpScore: 0.72, calendarScore: 0.35, combinedScore: 0.81, signal: 'STRONG_BUY', confidence: 0.89, conflictFlag: false, newsCount: 47, redditCount: 312, change24h: 0.024 },
  { ticker: 'MSFT', companyName: 'Microsoft Corp.', sector: 'Technology', marketCap: 3.12e12, sp500Rank: 2, nlpScore: 0.65, calendarScore: 0.28, combinedScore: 0.74, signal: 'BUY', confidence: 0.82, conflictFlag: false, newsCount: 38, redditCount: 189, change24h: 0.018 },
  { ticker: 'NVDA', companyName: 'NVIDIA Corp.', sector: 'Technology', marketCap: 2.89e12, sp500Rank: 3, nlpScore: 0.88, calendarScore: 0.12, combinedScore: 0.78, signal: 'BUY', confidence: 0.76, conflictFlag: true, newsCount: 62, redditCount: 534, change24h: 0.042 },
  { ticker: 'AMZN', companyName: 'Amazon.com Inc.', sector: 'Consumer Cyclical', marketCap: 2.15e12, sp500Rank: 4, nlpScore: 0.41, calendarScore: 0.55, combinedScore: 0.62, signal: 'HOLD', confidence: 0.71, conflictFlag: false, newsCount: 29, redditCount: 201, change24h: -0.008 },
  { ticker: 'GOOGL', companyName: 'Alphabet Inc.', sector: 'Technology', marketCap: 2.08e12, sp500Rank: 5, nlpScore: 0.55, calendarScore: 0.42, combinedScore: 0.68, signal: 'BUY', confidence: 0.78, conflictFlag: false, newsCount: 33, redditCount: 156, change24h: 0.011 },
  { ticker: 'META', companyName: 'Meta Platforms', sector: 'Technology', marketCap: 1.62e12, sp500Rank: 6, nlpScore: -0.22, calendarScore: 0.38, combinedScore: 0.42, signal: 'HOLD', confidence: 0.65, conflictFlag: true, newsCount: 41, redditCount: 278, change24h: -0.015 },
  { ticker: 'TSLA', companyName: 'Tesla Inc.', sector: 'Consumer Cyclical', marketCap: 1.25e12, sp500Rank: 7, nlpScore: -0.45, calendarScore: 0.15, combinedScore: 0.28, signal: 'AVOID', confidence: 0.83, conflictFlag: false, newsCount: 58, redditCount: 891, change24h: -0.032 },
  { ticker: 'BRK.B', companyName: 'Berkshire Hathaway', sector: 'Financials', marketCap: 1.08e12, sp500Rank: 8, nlpScore: 0.31, calendarScore: 0.62, combinedScore: 0.65, signal: 'BUY', confidence: 0.74, conflictFlag: false, newsCount: 12, redditCount: 67, change24h: 0.006 },
  { ticker: 'JPM', companyName: 'JPMorgan Chase', sector: 'Financials', marketCap: 0.72e12, sp500Rank: 9, nlpScore: 0.48, calendarScore: 0.51, combinedScore: 0.69, signal: 'BUY', confidence: 0.77, conflictFlag: false, newsCount: 24, redditCount: 98, change24h: 0.014 },
  { ticker: 'V', companyName: 'Visa Inc.', sector: 'Financials', marketCap: 0.62e12, sp500Rank: 10, nlpScore: 0.38, calendarScore: 0.44, combinedScore: 0.58, signal: 'HOLD', confidence: 0.69, conflictFlag: false, newsCount: 15, redditCount: 43, change24h: 0.003 },
]

function generateSentimentHistory(): SentimentHistory[] {
  const history: SentimentHistory[] = []
  const now = new Date()
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    const base = Math.sin(i * 0.3) * 0.3
    history.push({
      date: date.toISOString().slice(0, 10),
      nlpScore: Math.max(-1, Math.min(1, base + 0.4 + (Math.random() - 0.5) * 0.2)),
      calendarScore: Math.max(-1, Math.min(1, 0.3 + Math.sin(i * 0.15) * 0.25)),
      combinedScore: Math.max(0, Math.min(1, 0.6 + base * 0.3 + (Math.random() - 0.5) * 0.1)),
      newsCount: Math.floor(20 + Math.random() * 40),
    })
  }
  return history
}

export const mockSentimentHistory: SentimentHistory[] = generateSentimentHistory()

export const mockExperiments: ExperimentWeek[] = [
  { weekNumber: 1, method: 'SEN2NAL', stocks: [{ ticker: 'AAPL', entryPrice: 185.2, exitPrice: 189.5, return: 0.023 }, { ticker: 'MSFT', entryPrice: 415.0, exitPrice: 421.3, return: 0.015 }], weeklyReturn: 0.019, isWinner: true },
  { weekNumber: 1, method: 'CHATGPT', stocks: [{ ticker: 'NVDA', entryPrice: 875.0, exitPrice: 882.1, return: 0.008 }, { ticker: 'GOOGL', entryPrice: 155.2, exitPrice: 154.8, return: -0.003 }], weeklyReturn: 0.003, isWinner: false },
  { weekNumber: 1, method: 'GEMINI', stocks: [{ ticker: 'TSLA', entryPrice: 245.0, exitPrice: 238.2, return: -0.028 }, { ticker: 'META', entryPrice: 505.3, exitPrice: 512.1, return: 0.013 }], weeklyReturn: -0.008, isWinner: false },
  { weekNumber: 1, method: 'GROK', stocks: [{ ticker: 'AMZN', entryPrice: 186.5, exitPrice: 188.9, return: 0.013 }, { ticker: 'JPM', entryPrice: 198.2, exitPrice: 196.5, return: -0.009 }], weeklyReturn: 0.002, isWinner: false },
  { weekNumber: 2, method: 'SEN2NAL', stocks: [{ ticker: 'GOOGL', entryPrice: 154.8, exitPrice: 158.2, return: 0.022 }, { ticker: 'JPM', entryPrice: 196.5, exitPrice: 201.3, return: 0.024 }], weeklyReturn: 0.023, isWinner: true },
  { weekNumber: 2, method: 'CHATGPT', stocks: [{ ticker: 'AAPL', entryPrice: 189.5, exitPrice: 191.2, return: 0.009 }, { ticker: 'V', entryPrice: 282.1, exitPrice: 285.4, return: 0.012 }], weeklyReturn: 0.011, isWinner: false },
  { weekNumber: 2, method: 'GEMINI', stocks: [{ ticker: 'MSFT', entryPrice: 421.3, exitPrice: 425.8, return: 0.011 }, { ticker: 'NVDA', entryPrice: 882.1, exitPrice: 895.3, return: 0.015 }], weeklyReturn: 0.013, isWinner: false },
  { weekNumber: 2, method: 'GROK', stocks: [{ ticker: 'TSLA', entryPrice: 238.2, exitPrice: 232.5, return: -0.024 }, { ticker: 'BRK.B', entryPrice: 438.5, exitPrice: 441.2, return: 0.006 }], weeklyReturn: -0.009, isWinner: false },
  { weekNumber: 3, method: 'SEN2NAL', stocks: [{ ticker: 'NVDA', entryPrice: 895.3, exitPrice: 912.8, return: 0.020 }, { ticker: 'BRK.B', entryPrice: 441.2, exitPrice: 445.6, return: 0.010 }], weeklyReturn: 0.015, isWinner: false },
  { weekNumber: 3, method: 'CHATGPT', stocks: [{ ticker: 'META', entryPrice: 512.1, exitPrice: 525.4, return: 0.026 }, { ticker: 'AMZN', entryPrice: 188.9, exitPrice: 192.1, return: 0.017 }], weeklyReturn: 0.022, isWinner: true },
  { weekNumber: 3, method: 'GEMINI', stocks: [{ ticker: 'AAPL', entryPrice: 191.2, exitPrice: 190.8, return: -0.002 }, { ticker: 'GOOGL', entryPrice: 158.2, exitPrice: 159.5, return: 0.008 }], weeklyReturn: 0.003, isWinner: false },
  { weekNumber: 3, method: 'GROK', stocks: [{ ticker: 'JPM', entryPrice: 201.3, exitPrice: 199.8, return: -0.007 }, { ticker: 'V', entryPrice: 285.4, exitPrice: 287.2, return: 0.006 }], weeklyReturn: -0.001, isWinner: false },
]

export const mockFearGreed: FearGreed = {
  score: 62,
  classification: 'Greed',
  prevScore: 55,
  change: 7,
}

function generatePipelineLogs(): PipelineLog[] {
  const stages = ['Ingestion', 'FinBERT', 'Calendar', 'Features', 'Prediction', 'Database']
  const messages = [
    'Fetched 47 articles from NewsAPI',
    'Processed Reddit batch: 312 posts',
    'FinBERT inference: 359 records, avg 0.13s/record',
    'Calendar patterns computed for 503 tickers',
    'Holiday decay applied: Memorial Day -0.15',
    'Feature vectors generated: 503 x 24 dimensions',
    'SHAP values computed for top 10 tickers',
    'XGBoost prediction: 503 tickers, 2.3s total',
    'Walk-forward window: 2024-W08 to 2024-W12',
    'Database write: 503 predictions committed',
    'Staging tables refreshed: news_raw, reddit_raw',
    'Pipeline complete: 47.2s total runtime',
  ]
  const now = new Date()
  return messages.map((message, i) => {
    const ts = new Date(now.getTime() - (messages.length - i) * 4000)
    return {
      timestamp: ts.toISOString(),
      stage: stages[Math.min(Math.floor(i / 2), stages.length - 1)],
      message,
      level: i === 4 ? 'warning' : i === messages.length - 1 ? 'success' : 'info',
    }
  })
}

export const mockPipelineLogs: PipelineLog[] = generatePipelineLogs()

export const mockPipelineStatuses: PipelineStatus[] = [
  { stage: 'Data Ingestion', status: 'complete', lastRun: new Date().toISOString(), duration: 12.4 },
  { stage: 'FinBERT NLP', status: 'complete', lastRun: new Date().toISOString(), duration: 18.7 },
  { stage: 'Feature Engineering', status: 'complete', lastRun: new Date().toISOString(), duration: 5.2 },
  { stage: 'XGBoost Prediction', status: 'complete', lastRun: new Date().toISOString(), duration: 2.3 },
  { stage: 'Output & Storage', status: 'running', lastRun: new Date().toISOString(), duration: 8.6 },
]
