import { useState, KeyboardEvent } from 'react'

interface Props {
  onSearch: (query: string) => void
  isLoading?: boolean
}

export default function SearchBar({ onSearch, isLoading }: Props) {
  const [query, setQuery] = useState('')

  const handleSearch = () => {
    const trimmed = query.trim()
    if (trimmed) onSearch(trimmed)
  }

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <div className="flex items-center gap-2 w-full max-w-2xl">
      <input
        className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
        placeholder="종목명 또는 티커 검색 (예: 삼성전자, AAPL, 005930)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKey}
        disabled={isLoading}
      />
      <button
        onClick={handleSearch}
        disabled={isLoading || !query.trim()}
        className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg font-medium transition-colors shrink-0"
      >
        {isLoading ? '검색 중...' : '검색'}
      </button>
    </div>
  )
}
