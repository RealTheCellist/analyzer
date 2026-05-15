import { useState, KeyboardEvent } from 'react'
import { Market } from '../types'

interface Props {
  onSearch: (ticker: string, market: Market) => void
  isLoading?: boolean
}

export default function SearchBar({ onSearch, isLoading }: Props) {
  const [query, setQuery] = useState('')
  const [market, setMarket] = useState<Market>('KR')

  const handleSearch = () => {
    const trimmed = query.trim()
    if (trimmed) onSearch(trimmed, market)
  }

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <div className="flex items-center gap-2 w-full max-w-2xl">
      {/* 시장 토글 */}
      <div className="flex rounded-lg overflow-hidden border border-gray-700 shrink-0">
        {(['KR', 'US'] as Market[]).map((m) => (
          <button
            key={m}
            onClick={() => setMarket(m)}
            className={`px-3 py-2 text-sm font-medium transition-colors ${
              market === m ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
            disabled={isLoading}
          >
            {m === 'KR' ? '국내' : '미국'}
          </button>
        ))}
      </div>

      {/* 입력창 */}
      <input
        className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
        placeholder={market === 'KR' ? '종목명 또는 티커 (예: 삼성전자, 005930)' : '티커 입력 (예: AAPL, TSLA)'}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKey}
        disabled={isLoading}
      />

      {/* 검색 버튼 */}
      <button
        onClick={handleSearch}
        disabled={isLoading || !query.trim()}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg font-medium transition-colors shrink-0"
      >
        {isLoading ? '검색 중...' : '검색'}
      </button>
    </div>
  )
}
