// API 응답에서 오는 market 값 (KR/US만 가능)
export type Market = 'KR' | 'US'
// 검색 파라미터용 (ALL 포함)
export type SearchMarket = 'KR' | 'US' | 'ALL'
export type QuoteType = 'EQUITY' | 'ETF'
export type Verdict = 'STRONG_BUY' | 'QUALIFIED' | 'WATCHLIST' | 'DISQUALIFIED'
export type Signal = 'BUY' | 'SELL' | 'NEUTRAL'
export type Recommendation = '강력매수' | '매수' | '분할매수' | '관망'
export type Sentiment = 'positive' | 'negative' | 'neutral'

export interface SearchResult {
  ticker: string
  name: string
  market: Market
  current_price: number
}

export interface FundamentalIndicator {
  name: string
  value: number | null
  benchmark: string
  pass: boolean
  weight: number
}

export interface TechnicalIndicator {
  name: string
  value: number | null
  signal: Signal
  score: number
}

export interface NewsKeyword {
  text: string
  value: number
  sentiment: Sentiment
}

export interface NewsItem {
  title: string
  link: string
  published: string
  source: string
}

export type PostCategory = '버그제보' | '기능제안' | '기타'

export interface Post {
  id: number
  category: PostCategory
  title: string
  content: string
  created_at: string
}

export interface PostListResponse {
  total: number
  page: number
  posts: Post[]
}

export interface AnalysisResult {
  ticker: string
  name: string
  market: Market
  quote_type: QuoteType
  current_price: number
  market_cap: number
  analyzed_at: string
  total_score: number
  verdict: Verdict
  recommendation: Recommendation
  breakdown: {
    fundamental: {
      score: number
      indicators: FundamentalIndicator[]
    }
    technical: {
      score: number
      indicators: TechnicalIndicator[]
    }
    sentiment: {
      sentiment_score: number
      news_score: number
      positive_ratio: number
      neutral_ratio: number
      negative_ratio: number
      summary: string
      bull_signals: string[]
      bear_signals: string[]
      keywords: NewsKeyword[]
    }
    ai: {
      score: number
      reasoning: string
      strengths: string[]
      weaknesses: string[]
    }
  }
  news: NewsItem[]
}
