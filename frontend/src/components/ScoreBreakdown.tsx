import { BarChart, Bar, XAxis, YAxis, Cell, ResponsiveContainer, Tooltip, LabelList } from 'recharts'
import { AnalysisResult } from '../types'

interface Props {
  breakdown: AnalysisResult['breakdown']
}

const WEIGHTS: Record<string, string> = {
  '재무': '30%', '기술': '20%', '뉴스/감성': '20%', 'AI': '30%',
}

function getColor(ratio: number) {
  if (ratio >= 0.7) return '#22c55e'
  if (ratio >= 0.4) return '#eab308'
  return '#ef4444'
}

export default function ScoreBreakdown({ breakdown }: Props) {
  const newsTotal = breakdown.sentiment.sentiment_score + breakdown.sentiment.news_score
  const items = [
    { name: '재무', score: breakdown.fundamental.score, max: 30 },
    { name: '기술', score: breakdown.technical.score, max: 20 },
    { name: '뉴스/감성', score: newsTotal, max: 20 },
    { name: 'AI', score: breakdown.ai.score, max: 30 },
  ]

  const data = items.map((item) => ({
    ...item,
    ratio: item.score / item.max,
    percent: Math.round((item.score / item.max) * 100),
    label: `${item.score}/${item.max}`,
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical" margin={{ left: 16, right: 40 }}>
        <XAxis type="number" domain={[0, 100]} hide />
        <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 13 }} width={36} />
        <Tooltip
          contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
          formatter={(_value: unknown, _name: unknown, props: { payload?: { name: string; score: number; max: number } }) => [
            `${props.payload?.score} / ${props.payload?.max}점 (비중 ${WEIGHTS[props.payload?.name ?? ''] ?? ''})`,
            '',
          ]}
        />
        <Bar dataKey="percent" radius={[0, 4, 4, 0]}>
          <LabelList dataKey="label" position="right" style={{ fill: '#9ca3af', fontSize: 12 }} />
          {data.map((entry, index) => (
            <Cell key={index} fill={getColor(entry.ratio)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
