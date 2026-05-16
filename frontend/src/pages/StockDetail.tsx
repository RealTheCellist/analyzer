import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { Market } from '../types'
import { runAnalysis } from '../api/stockApi'
import { formatPrice, formatMarketCap } from '../utils/format'
import LoadingSpinner from '../components/LoadingSpinner'
import VerdictBadge from '../components/VerdictBadge'
import ScoreGauge from '../components/ScoreGauge'
import RadarChart from '../components/RadarChart'
import ScoreBreakdown from '../components/ScoreBreakdown'
import NewsPanel from '../components/NewsPanel'
import SentimentBubble from '../components/SentimentBubble'

function SignalBadge({ signal }: { signal: string }) {
  const cfg = {
    BUY: 'bg-green-500/20 text-green-400 border-green-500/30',
    SELL: 'bg-red-500/20 text-red-400 border-red-500/30',
    NEUTRAL: 'bg-gray-700 text-gray-400 border-gray-600',
  }
  const cls = cfg[signal as keyof typeof cfg] ?? cfg.NEUTRAL
  return <span className={`text-xs px-2 py-0.5 rounded border font-medium ${cls}`}>{signal}</span>
}

const VALID_MARKETS = new Set<string>(['KR', 'US'])

function _formatIndicatorValue(name: string, value: number, market?: string): string {
  if (name === 'AUM(운용규모)') {
    if (market === 'KR') {
      if (value >= 1_000_000_000_000) return `${(value / 1_000_000_000_000).toFixed(1)}조`
      if (value >= 100_000_000) return `${(value / 100_000_000).toFixed(0)}억`
      return `${value.toFixed(0)}원`
    }
    if (value >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(1)}T`
    if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(0)}M`
    return `$${value.toFixed(0)}`
  }
  if (name === '운용보수' || name === '분배율(배당)' || name === '3년수익률') {
    return `${value.toFixed(2)}%`
  }
  return value.toFixed(2)
}

export default function StockDetail() {
  const { market, ticker } = useParams<{ market: string; ticker: string }>()
  const navigate = useNavigate()

  const isValidParams = !!ticker && !!market && VALID_MARKETS.has(market)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['analysis', market, ticker],
    queryFn: () => runAnalysis(ticker!, market as Market),
    enabled: isValidParams,
    staleTime: 5 * 60 * 1000,
  })

  if (!isValidParams) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-red-400 text-lg">잘못된 URL입니다.</p>
        <button
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-white text-sm"
          onClick={() => navigate('/')}
        >
          홈으로 돌아가기
        </button>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" text="AI 분석 중... (최대 1분 소요)" />
      </div>
    )
  }

  if (isError || !data) {
    const errorMsg = axios.isAxiosError(error)
      ? (error.response?.data?.detail ?? '서버 오류가 발생했습니다.')
      : '분석 중 오류가 발생했습니다.'

    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-red-400 text-lg">분석 중 오류가 발생했습니다.</p>
        <p className="text-gray-500 text-sm">{errorMsg}</p>
        <button
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-white text-sm"
          onClick={() => navigate('/')}
        >
          홈으로 돌아가기
        </button>
      </div>
    )
  }

  const { breakdown } = data

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 flex flex-col gap-6">
      {/* 뒤로가기 */}
      <button
        className="self-start text-gray-400 hover:text-white text-sm flex items-center gap-1 transition-colors"
        onClick={() => navigate('/')}
      >
        ← 홈으로
      </button>

      {/* 종목 헤더 */}
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {data.name}
            <span className="ml-2 text-gray-500 text-lg font-normal">({data.ticker})</span>
            <span className="ml-2 text-sm bg-gray-700 text-gray-300 px-2 py-0.5 rounded">{data.market}</span>
            {data.quote_type === 'ETF' && (
              <span className="ml-2 text-sm bg-purple-500/20 text-purple-400 border border-purple-500/30 px-2 py-0.5 rounded">ETF</span>
            )}
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            현재가: <span className="text-white font-mono">{formatPrice(data.current_price, data.market)}</span>
            {' · '}시가총액: <span className="text-white">{formatMarketCap(data.market_cap, data.market)}</span>
          </p>
        </div>
        <VerdictBadge verdict={data.verdict} />
      </div>

      {/* 레이더 + 게이지 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-xl p-4">
          <h2 className="text-sm font-semibold text-gray-400 mb-2">영역별 분석</h2>
          <RadarChart
            fundamental={breakdown.fundamental.score}
            technical={breakdown.technical.score}
            sentiment={breakdown.sentiment.sentiment_score}
            news={breakdown.sentiment.news_score}
            ai={breakdown.ai.score}
          />
        </div>
        <div className="bg-gray-900 rounded-xl p-4 flex flex-col items-center justify-center gap-4">
          <ScoreGauge score={data.total_score} verdict={data.verdict} />
          <div className="text-center">
            <p className="text-gray-400 text-xs mb-1">추천</p>
            <span className={`text-xl font-bold ${
              data.recommendation === '강력매수' ? 'text-emerald-400' :
              data.recommendation === '매수' ? 'text-green-400' :
              data.recommendation === '분할매수' ? 'text-blue-400' : 'text-gray-400'
            }`}>
              {data.recommendation}
            </span>
          </div>
          <p className="text-gray-400 text-sm text-center px-2">{breakdown.ai.reasoning}</p>
        </div>
      </div>

      {/* 점수 막대 */}
      <div className="bg-gray-900 rounded-xl p-4">
        <h2 className="text-sm font-semibold text-gray-400 mb-3">영역별 점수</h2>
        <ScoreBreakdown breakdown={breakdown} />
      </div>

      {/* 강점 / 약점 */}
      {(breakdown.ai.strengths.length > 0 || breakdown.ai.weaknesses.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-900 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-green-400 mb-3">강점</h2>
            <ul className="flex flex-col gap-2">
              {breakdown.ai.strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <span className="text-green-400 mt-0.5">✓</span>{s}
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-gray-900 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-red-400 mb-3">약점</h2>
            <ul className="flex flex-col gap-2">
              {breakdown.ai.weaknesses.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <span className="text-red-400 mt-0.5">⚠</span>{s}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* 재무/ETF 지표 */}
      <div className="bg-gray-900 rounded-xl p-4">
        <h2 className="text-sm font-semibold text-gray-400 mb-3">
          {data.quote_type === 'ETF' ? 'ETF 지표 상세' : '재무 지표 상세'}
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {breakdown.fundamental.indicators.map((ind) => (
            <div key={ind.name} className={`bg-gray-800 rounded-lg p-3 border ${ind.pass ? 'border-green-500/20' : 'border-gray-700'}`}>
              <p className="text-xs text-gray-500 mb-1">{ind.name}</p>
              <p className="text-white font-mono font-semibold text-sm">
                {ind.value != null ? _formatIndicatorValue(ind.name, ind.value, data.market) : '-'}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">{ind.benchmark}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 기술 지표 */}
      <div className="bg-gray-900 rounded-xl p-4">
        <h2 className="text-sm font-semibold text-gray-400 mb-3">기술적 지표</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {breakdown.technical.indicators.map((ind) => (
            <div key={ind.name} className="bg-gray-800 rounded-lg p-3 flex flex-col gap-1">
              <p className="text-xs text-gray-500">{ind.name}</p>
              <p className="text-white font-mono text-sm">
                {ind.value != null ? ind.value.toFixed(2) : '-'}
              </p>
              <SignalBadge signal={ind.signal} />
            </div>
          ))}
        </div>
      </div>

      {/* 감성 버블 + 뉴스 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-xl p-4">
          <h2 className="text-sm font-semibold text-gray-400 mb-3">감성 키워드</h2>
          <SentimentBubble keywords={breakdown.sentiment.keywords} />
        </div>
        <div className="bg-gray-900 rounded-xl p-4">
          <h2 className="text-sm font-semibold text-gray-400 mb-3">최신 뉴스</h2>
          <NewsPanel news={data.news} sentiment={breakdown.sentiment} />
        </div>
      </div>
    </div>
  )
}
