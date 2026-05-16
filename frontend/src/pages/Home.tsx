import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { SearchResult } from '../types'
import { searchStocks } from '../api/stockApi'
import { formatPrice } from '../utils/format'
import SearchBar from '../components/SearchBar'

const RECENT_KEY = 'recent_stocks'

const VALID_MARKETS = new Set<string>(['KR', 'US'])

function isSearchResult(obj: unknown): obj is SearchResult {
  if (typeof obj !== 'object' || obj === null) return false
  const r = obj as Record<string, unknown>
  return (
    typeof r.ticker === 'string' &&
    typeof r.name === 'string' &&
    typeof r.market === 'string' && VALID_MARKETS.has(r.market) &&
    typeof r.current_price === 'number'
  )
}

function getRecent(): SearchResult[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
    if (!Array.isArray(parsed)) return []
    return parsed.filter(isSearchResult)
  } catch {
    return []
  }
}

function saveRecent(item: SearchResult) {
  const prev = getRecent().filter((r) => !(r.ticker === item.ticker && r.market === item.market))
  const next = [item, ...prev].slice(0, 5)
  localStorage.setItem(RECENT_KEY, JSON.stringify(next))
}

export default function Home() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [recent, setRecent] = useState<SearchResult[]>(getRecent)

  const { data: results, isFetching, isError: isSearchError } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: () => searchStocks(searchQuery, 'ALL'),
    enabled: searchQuery.length > 0,
    staleTime: 30 * 1000,
  })

  const handleSearch = (q: string) => {
    setSearchQuery(q)
  }

  const handleSelect = (item: SearchResult) => {
    saveRecent(item)
    setRecent(getRecent())
    navigate(`/stock/${item.market}/${item.ticker}`)
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-2xl flex flex-col items-center gap-8">
        {/* 헤더 */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white mb-2">주식 투자 적합도 분석기</h1>
          <p className="text-gray-400">국내·미국 주식을 0~100점으로 분석합니다</p>
          <div className="mt-3 flex gap-2 justify-center">
            <button
              className="text-sm px-4 py-1.5 rounded-full border border-blue-500/40 text-blue-400 hover:bg-blue-500/10 transition-colors"
              onClick={() => navigate('/compare')}
            >
              ⇄ 종목 비교 분석
            </button>
            <button
              className="text-sm px-4 py-1.5 rounded-full border border-gray-600 text-gray-400 hover:bg-gray-800 transition-colors"
              onClick={() => navigate('/board')}
            >
              ✉ 버그제보 / 기능제안
            </button>
          </div>
        </div>

        {/* 검색창 */}
        <SearchBar onSearch={handleSearch} isLoading={isFetching} />

        {/* 검색 결과 */}
        {results && results.length > 0 && (
          <div className="w-full rounded-xl border border-gray-800 overflow-hidden">
            {results.map((item) => (
              <button
                key={`${item.market}-${item.ticker}`}
                className="w-full flex items-center justify-between px-4 py-3 bg-gray-900 hover:bg-gray-800 border-b border-gray-800 last:border-0 transition-colors text-left"
                onClick={() => handleSelect(item)}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300">{item.market}</span>
                  <span className="font-medium text-white">{item.name}</span>
                  <span className="text-gray-500 text-sm">{item.ticker}</span>
                </div>
                <span className="text-blue-400 font-mono text-sm">{formatPrice(item.current_price, item.market)}</span>
              </button>
            ))}
          </div>
        )}

        {isSearchError && (
          <p className="text-red-400 text-sm">검색 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.</p>
        )}

        {results && results.length === 0 && searchQuery && !isFetching && (
          <p className="text-gray-500 text-sm">검색 결과가 없습니다.</p>
        )}

        {/* 최근 검색 */}
        {recent.length > 0 && !searchQuery && (
          <div className="w-full">
            <p className="text-xs text-gray-500 mb-2 px-1">최근 검색</p>
            <div className="flex flex-wrap gap-2">
              {recent.map((item) => (
                <button
                  key={`${item.market}-${item.ticker}`}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-full text-sm text-gray-300 transition-colors border border-gray-700"
                  onClick={() => handleSelect(item)}
                >
                  <span className="text-xs text-gray-500">{item.market}</span>
                  {item.name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 면책 문구 */}
      <p className="mt-12 text-center text-sm text-gray-600 max-w-lg leading-relaxed">
        본 서비스는 투자 참고용 정보를 제공하며, 투자 권유나 자문이 아닙니다.<br />
        분석 결과에 따른 투자 손익에 대해 어떠한 법적 책임도 지지 않습니다.
      </p>
    </div>
  )
}
