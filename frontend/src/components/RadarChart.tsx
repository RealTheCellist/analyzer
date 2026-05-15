import {
  RadarChart as ReRadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

interface Props {
  fundamental: number
  technical: number
  sentiment: number
  news: number
  ai: number
}

export default function RadarChart({ fundamental, technical, sentiment, news, ai }: Props) {
  const data = [
    { subject: '재무', value: Math.round((fundamental / 30) * 100), fullMark: 100 },
    { subject: '기술', value: Math.round((technical / 20) * 100), fullMark: 100 },
    { subject: '뉴스/감성', value: Math.round(((sentiment + news) / 20) * 100), fullMark: 100 },
    { subject: 'AI', value: Math.round((ai / 30) * 100), fullMark: 100 },
  ]

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ReRadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
        <PolarGrid stroke="#374151" />
        <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 13 }} />
        <Radar
          name="점수"
          dataKey="value"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.35}
          strokeWidth={2}
        />
        <Tooltip
          contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
          formatter={(val: number) => [`${val}%`, '달성률']}
        />
      </ReRadarChart>
    </ResponsiveContainer>
  )
}
