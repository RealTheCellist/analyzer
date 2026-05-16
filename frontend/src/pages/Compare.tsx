import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { AnalysisResult, SearchResult } from '../types'
import { searchStocks, runAnalysis } from '../api/stockApi'
import { formatPrice, formatMarketCap } from '../utils/format'
import LoadingSpinner from '../components/LoadingSpinner'
import VerdictBadge from '../components/VerdictBadge'
import ScoreGauge from '../components/ScoreGauge'

function SearchSlot({
  label,
  selected,
  onSelect,
  onClear,
}: {
  label: string
  selected: SearchResult | null
  onSelect: (item: SearchResult) => void
  onClear: () => void
}) {
  const [query, setQuery] = useState('')

  const { data: results, isFetching } = useQuery({
    queryKey: ['search', query, 'ALL'],
    queryFn: () => searchStocks(query, 'ALL'),
    enabled: query.length > 0,
    staleTime: 30_000,
  })

  return (
    <div className="flex-1 flex flex-col gap-3">
      <p className="text-sm font-semibold text-gray-400">{label}</p>

      {selected ? (
        <div className="bg-gray-800 rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-white font-semibold">{selected.name}</p>
            <p className="text-gray-400 text-sm">{selected.ticker} · {selected.market}</p>
          </div>
          <button
            className="text-xs text-gray-500 hover:text-red-400 transition-colors"
            onClick={() => { setQuery(''); onClear(); }}
          >
            변경
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <input
            type="text"
            placeholder="종목명 또는 티커 검색..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-gray-800 text-white text-sm rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-blue-500"
          />
          {isFetching && <p className="text-xs text-gray-500 px-1">검색 중...</p>}
          {results && results.length > 0 && (
            <div className="rounded-xl border border-gray-700 overflow-hidden">
              {results.slice(0, 8).map((item) => (
                <button
                  key={`${item.market}-${item.ticker}`}
                  className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-900 hover:bg-gray-800 border-b border-gray-800 last:border-0 text-left transition-colors"
                  onClick={() => { onSelect(item); setQuery(''); }}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-400">{item.market}</span>
                    <span className="text-white text-sm">{item.name}</span>
                    <span className="text-gray-500 text-xs">{item.ticker}</span>
                  </div>
                  <span className="text-blue-400 font-mono text-xs">{formatPrice(item.current_price, item.market)}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function getColor(verdict: string) {
  if (verdict === 'STRONG_BUY') return 'text-emerald-400'
  if (verdict === 'QUALIFIED') return 'text-green-400'
  if (verdict === 'WATCHLIST') return 'text-blue-400'
  return 'text-gray-400'
}

function CompareRow({
  label,
  left,
  right,
  format = (v: number) => v.toFixed(2),
  higherIsBetter = true,
}: {
  label: string
  left: number | null
  right: number | null
  format?: (v: number) => string
  higherIsBetter?: boolean
}) {
  const leftWins = left != null && right != null && (higherIsBetter ? left > right : left < right)
  const rightWins = left != null && right != null && (higherIsBetter ? right > left : right < left)

  return (
    <div className="grid grid-cols-3 items-center py-2.5 border-b border-gray-800 last:border-0">
      <span className={`text-right font-mono text-sm pr-4 ${leftWins ? 'text-green-400 font-bold' : 'text-gray-300'}`}>
        {left != null ? format(left) : '-'}
        {leftWins && <span className="ml-1 text-green-400">◀</span>}
      </span>
      <span className="text-center text-xs text-gray-500">{label}</span>
      <span className={`text-left font-mono text-sm pl-4 ${rightWins ? 'text-green-400 font-bold' : 'text-gray-300'}`}>
        {rightWins && <span className="mr-1 text-green-400">▶</span>}
        {right != null ? format(right) : '-'}
      </span>
    </div>
  )
}

export default function Compare() {
  const navigate = useNavigate()
  const [leftStock, setLeftStock] = useState<SearchResult | null>(null)
  const [rightStock, setRightStock] = useState<SearchResult | null>(null)

  const leftQuery = useQuery<AnalysisResult>({
    queryKey: ['analysis', leftStock?.market, leftStock?.ticker],
    queryFn: () => runAnalysis(leftStock!.ticker, leftStock!.market),
    enabled: !!leftStock,
    staleTime: 5 * 60_000,
  })

  const rightQuery = useQuery<AnalysisResult>({
    queryKey: ['analysis', rightStock?.market, rightStock?.ticker],
    queryFn: () => runAnalysis(rightStock!.ticker, rightStock!.market),
    enabled: !!rightStock,
    staleTime: 5 * 60_000,
  })

  const L = leftQuery.data
  const R = rightQuery.data
  const isLoading = leftQuery.isLoading || rightQuery.isLoading

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex flex-col gap-6">
      <button
        className="self-start text-gray-400 hover:text-white text-sm flex items-center gap-1 transition-colors"
        onClick={() => navigate('/')}
      >
        ← 홈으로
      </button>

      <h1 className="text-2xl font-bold text-white">종목 비교 분석</h1>

      {/* 종목 선택 */}
      <div className="flex gap-4">
        <SearchSlot label="종목 A" selected={leftStock} onSelect={setLeftStock} onClear={() => setLeftStock(null)} />
        <div className="flex items-center pt-8 text-gray-600 font-bold text-xl">VS</div>
        <SearchSlot label="종목 B" selected={rightStock} onSelect={setRightStock} onClear={() => setRightStock(null)} />
      </div>

      {/* 로딩 */}
      {isLoading && (
        <div className="flex justify-center py-16">
          <LoadingSpinner size="lg" text="AI 분석 중..." />
        </div>
      )}

      {/* 비교 결과 */}
      {L && R && !isLoading && (
        <div className="flex flex-col gap-4">
          {/* 헤더 */}
          <div className="grid grid-cols-3 text-center">
            <div className="flex flex-col items-center gap-2">
              <p className="text-white font-bold text-lg">{L.name}</p>
              <p className="text-gray-500 text-sm">{L.ticker} · {L.market}</p>
              <VerdictBadge verdict={L.verdict} />
            </div>
            <div className="flex items-center justify-center text-gray-600 font-bold text-2xl">VS</div>
            <div className="flex flex-col items-center gap-2">
              <p className="text-white font-bold text-lg">{R.name}</p>
              <p className="text-gray-500 text-sm">{R.ticker} · {R.market}</p>
              <VerdictBadge verdict={R.verdict} />
            </div>
          </div>

          {/* 총점 게이지 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-900 rounded-xl p-4 flex flex-col items-center gap-2">
              <ScoreGauge score={L.total_score} verdict={L.verdict} />
              <span className={`text-lg font-bold ${getColor(L.verdict)}`}>{L.recommendation}</span>
            </div>
            <div className="bg-gray-900 rounded-xl p-4 flex flex-col items-center gap-2">
              <ScoreGauge score={R.total_score} verdict={R.verdict} />
              <span className={`text-lg font-bold ${getColor(R.verdict)}`}>{R.recommendation}</span>
            </div>
          </div>

          {/* 점수 비교 */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-gray-400 mb-3 text-center">영역별 점수 비교</h2>
            <CompareRow label="총점" left={L.total_score} right={R.total_score} format={(v) => `${v}점`} />
            <CompareRow label="재무 (/30)" left={L.breakdown.fundamental.score} right={R.breakdown.fundamental.score} />
            <CompareRow label="기술 (/20)" left={L.breakdown.technical.score} right={R.breakdown.technical.score} />
            <CompareRow
              label="뉴스/감성 (/20)"
              left={L.breakdown.sentiment.sentiment_score + L.breakdown.sentiment.news_score}
              right={R.breakdown.sentiment.sentiment_score + R.breakdown.sentiment.news_score}
            />
            <CompareRow label="AI (/30)" left={L.breakdown.ai.score} right={R.breakdown.ai.score} />
          </div>

          {/* 재무/ETF 지표 비교 */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-gray-400 mb-3 text-center">지표 비교</h2>
            {(() => {
              const allNames = Array.from(new Set([
                ...L.breakdown.fundamental.indicators.map((i) => i.name),
                ...R.breakdown.fundamental.indicators.map((i) => i.name),
              ]))
              const lowerIsBetter = new Set(['PER', 'PBR', '부채비율', '운용보수'])
              const leftMarket = L.market
              const rightMarket = R.market
              return allNames.map((name) => {
                const lInd = L.breakdown.fundamental.indicators.find((i) => i.name === name)
                const rInd = R.breakdown.fundamental.indicators.find((i) => i.name === name)
                const isAum = name === 'AUM(운용규모)'
                return (
                  <CompareRow
                    key={name}
                    label={name}
                    left={lInd?.value ?? null}
                    right={rInd?.value ?? null}
                    higherIsBetter={!lowerIsBetter.has(name)}
                    format={isAum
                      ? (v: number) => formatMarketCap(v, lInd != null ? leftMarket : rightMarket)
                      : undefined}
                  />
                )
              })
            })()}
          </div>

          {/* AI 분석 비교 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-900 rounded-xl p-4">
              <h2 className="text-sm font-semibold text-gray-400 mb-2">{L.name} AI 분석</h2>
              <p className="text-gray-300 text-sm mb-3">{L.breakdown.ai.reasoning}</p>
              <div className="flex flex-col gap-1">
                {L.breakdown.ai.strengths.map((s, i) => (
                  <p key={i} className="text-green-400 text-xs flex gap-1"><span>✓</span>{s}</p>
                ))}
                {L.breakdown.ai.weaknesses.map((s, i) => (
                  <p key={i} className="text-red-400 text-xs flex gap-1"><span>⚠</span>{s}</p>
                ))}
              </div>
            </div>
            <div className="bg-gray-900 rounded-xl p-4">
              <h2 className="text-sm font-semibold text-gray-400 mb-2">{R.name} AI 분석</h2>
              <p className="text-gray-300 text-sm mb-3">{R.breakdown.ai.reasoning}</p>
              <div className="flex flex-col gap-1">
                {R.breakdown.ai.strengths.map((s, i) => (
                  <p key={i} className="text-green-400 text-xs flex gap-1"><span>✓</span>{s}</p>
                ))}
                {R.breakdown.ai.weaknesses.map((s, i) => (
                  <p key={i} className="text-red-400 text-xs flex gap-1"><span>⚠</span>{s}</p>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 한 쪽만 선택된 경우 */}
      {(leftStock || rightStock) && !(L && R) && !isLoading && (
        <p className="text-center text-gray-500 text-sm py-8">종목을 2개 모두 선택하면 비교 분석을 시작합니다.</p>
      )}

      {!leftStock && !rightStock && (
        <p className="text-center text-gray-500 text-sm py-8">비교할 종목 2개를 검색해서 선택하세요.</p>
      )}
    </div>
  )
}
