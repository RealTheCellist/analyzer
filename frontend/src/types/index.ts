export type Market = 'KR' | 'US'
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

export interface AnalysisResult {
  ticker: string
  name: string
  market: Market
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
