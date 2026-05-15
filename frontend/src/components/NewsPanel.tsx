import { AnalysisResult, NewsItem } from '../types'

interface Props {
  news: NewsItem[]
  sentiment: AnalysisResult['breakdown']['sentiment']
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso
  }
}

export default function NewsPanel({ news, sentiment }: Props) {
  const pos = Math.round(sentiment.positive_ratio * 100)
  const neu = Math.round(sentiment.neutral_ratio * 100)
  const neg = Math.round(sentiment.negative_ratio * 100)

  return (
    <div className="flex flex-col gap-4">
      {/* 감성 비율 바 */}
      <div>
        <div className="flex text-xs text-gray-400 mb-1 gap-3">
          <span className="text-green-400">긍정 {pos}%</span>
          <span className="text-gray-400">중립 {neu}%</span>
          <span className="text-red-400">부정 {neg}%</span>
        </div>
        <div className="flex h-2 rounded-full overflow-hidden">
          <div className="bg-green-500" style={{ width: `${pos}%` }} />
          <div className="bg-gray-500" style={{ width: `${neu}%` }} />
          <div className="bg-red-500" style={{ width: `${neg}%` }} />
        </div>
      </div>

      {/* 요약 */}
      <p className="text-sm text-gray-300">{sentiment.summary}</p>

      {/* 신호 */}
      {(sentiment.bull_signals.length > 0 || sentiment.bear_signals.length > 0) && (
        <div className="flex gap-3 flex-wrap">
          {sentiment.bull_signals.map((s, i) => (
            <span key={i} className="text-xs bg-green-500/10 text-green-400 border border-green-500/20 px-2 py-0.5 rounded">
              ↑ {s}
            </span>
          ))}
          {sentiment.bear_signals.map((s, i) => (
            <span key={i} className="text-xs bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded">
              ↓ {s}
            </span>
          ))}
        </div>
      )}

      {/* 뉴스 목록 */}
      <div className="flex flex-col gap-2">
        {news.length === 0 ? (
          <p className="text-gray-500 text-sm">수집된 뉴스가 없습니다.</p>
        ) : (
          news.slice(0, 10).map((item, i) => (
            <a
              key={i}
              href={item.link.startsWith('http://') || item.link.startsWith('https://') ? item.link : '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col gap-0.5 p-2 rounded-lg bg-gray-800/60 hover:bg-gray-700/60 transition-colors"
            >
              <span className="text-sm text-gray-200 line-clamp-2">{item.title}</span>
              <span className="text-xs text-gray-500">
                {item.source} · {formatDate(item.published)}
              </span>
            </a>
          ))
        )}
      </div>
    </div>
  )
}
