import { useMemo } from 'react'
import { Wordcloud } from '@visx/wordcloud'
import { scaleLog } from '@visx/scale'
import { NewsKeyword } from '../types'

interface Props {
  keywords: NewsKeyword[]
}

const sentimentColor: Record<string, string> = {
  positive: '#22c55e',
  negative: '#ef4444',
  neutral: '#94a3b8',
}

export default function SentimentBubble({ keywords }: Props) {
  const keywordMap = useMemo(
    () => new Map(keywords.map((k) => [k.text, k.sentiment])),
    [keywords]
  )

  if (keywords.length === 0) {
    return <p className="text-gray-500 text-sm text-center py-8">키워드 없음</p>
  }

  const maxVal = Math.max(...keywords.map((k) => k.value))
  const minVal = Math.min(...keywords.map((k) => k.value))

  const fontScale = scaleLog({
    domain: [Math.max(1, minVal), Math.max(2, maxVal)],
    range: [12, 36],
  })

  const words = keywords.map((k) => ({ text: k.text, value: k.value, sentiment: k.sentiment }))

  return (
    <div className="flex justify-center">
      <Wordcloud
        words={words}
        width={320}
        height={200}
        fontSize={(w) => fontScale(w.value)}
        font="sans-serif"
        padding={3}
        rotate={0}
        spiral="archimedean"
      >
        {(cloudWords) =>
          cloudWords.map((w, i) => {
            const color = sentimentColor[keywordMap.get(w.text ?? '') ?? 'neutral']
            return (
              <text
                key={i}
                transform={`translate(${w.x}, ${w.y}) rotate(${w.rotate})`}
                style={{ fontSize: w.size, fontFamily: w.font, fill: color, cursor: 'default' }}
                textAnchor="middle"
              >
                {w.text}
              </text>
            )
          })
        }
      </Wordcloud>
    </div>
  )
}
