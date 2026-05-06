import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { COLORS } from '@/lib/constants'
import type { StockSentiment } from '@/types'

interface Props {
  stocks: StockSentiment[]
}

interface TreemapBlock {
  stock: StockSentiment
  x: number
  y: number
  w: number
  h: number
}

function computeLayout(stocks: StockSentiment[], width: number, height: number): TreemapBlock[] {
  const totalCap = stocks.reduce((sum, s) => sum + s.marketCap, 0)
  const blocks: TreemapBlock[] = []
  let x = 0
  let y = 0
  let remainingW = width
  let remainingH = height

  const sorted = [...stocks].sort((a, b) => b.marketCap - a.marketCap)

  for (let i = 0; i < sorted.length; i++) {
    const ratio = sorted[i].marketCap / totalCap
    const isHorizontal = remainingW >= remainingH

    if (isHorizontal) {
      const w = remainingW * ratio * (sorted.length / (sorted.length - i))
      const cappedW = Math.min(w, remainingW)
      blocks.push({ stock: sorted[i], x, y, w: cappedW, h: remainingH })
      x += cappedW
      remainingW -= cappedW
    } else {
      const h = remainingH * ratio * (sorted.length / (sorted.length - i))
      const cappedH = Math.min(h, remainingH)
      blocks.push({ stock: sorted[i], x, y, w: remainingW, h: cappedH })
      y += cappedH
      remainingH -= cappedH
    }
  }

  return blocks
}

function sentimentToColor(combinedScore: number): string {
  if (combinedScore >= 0.7) return COLORS.bullish
  if (combinedScore >= 0.5) return COLORS.cyan
  if (combinedScore >= 0.35) return COLORS.warning
  return COLORS.bearish
}

export default function SentimentTreemap({ stocks }: Props) {
  const width = 600
  const height = 300
  const blocks = useMemo(() => computeLayout(stocks, width, height), [stocks])

  return (
    <div className="bg-nightops-card border border-nightops-border rounded-lg p-4">
      <h3 className="text-sm font-header font-semibold text-nightops-text mb-3">
        Sentiment Treemap — Top 10 by Market Cap
      </h3>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 300 }}>
        {blocks.map((block, i) => {
          const color = sentimentToColor(block.stock.combinedScore)
          const showLabel = block.w > 40 && block.h > 30
          return (
            <motion.g
              key={block.stock.ticker}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05, duration: 0.3 }}
            >
              <rect
                x={block.x + 1}
                y={block.y + 1}
                width={Math.max(0, block.w - 2)}
                height={Math.max(0, block.h - 2)}
                fill={color}
                fillOpacity={0.2}
                stroke={color}
                strokeWidth={1}
                rx={4}
              />
              {showLabel && (
                <>
                  <text
                    x={block.x + block.w / 2}
                    y={block.y + block.h / 2 - 6}
                    textAnchor="middle"
                    fill="#F1F5F9"
                    fontSize={block.w > 80 ? 14 : 10}
                    fontFamily="Space Grotesk"
                    fontWeight="bold"
                  >
                    {block.stock.ticker}
                  </text>
                  <text
                    x={block.x + block.w / 2}
                    y={block.y + block.h / 2 + 10}
                    textAnchor="middle"
                    fill={color}
                    fontSize={block.w > 80 ? 12 : 9}
                    fontFamily="JetBrains Mono"
                  >
                    {(block.stock.change24h >= 0 ? '+' : '')}{(block.stock.change24h * 100).toFixed(1)}%
                  </text>
                </>
              )}
            </motion.g>
          )
        })}
      </svg>
    </div>
  )
}
