import axios from 'axios'
import { SearchResult, AnalysisResult, Market, SearchMarket, Post, PostListResponse, PostCategory } from '../types'

const api = axios.create({ baseURL: '/api' })

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      error.message = error.response.data.detail
    }
    return Promise.reject(error)
  }
)

export const searchStocks = async (query: string, market: SearchMarket): Promise<SearchResult[]> => {
  const { data } = await api.get('/stocks/search', { params: { q: query, market } })
  return data.results
}

export const runAnalysis = async (ticker: string, market: Market): Promise<AnalysisResult> => {
  const { data } = await api.post('/analysis/run', { ticker, market })
  return data
}

export const fetchPosts = async (page = 1): Promise<PostListResponse> => {
  const { data } = await api.get('/board/posts', { params: { page, limit: 20 } })
  return data
}

export const fetchPost = async (id: number): Promise<Post> => {
  const { data } = await api.get(`/board/posts/${id}`)
  return data
}

export const createPost = async (body: { category: PostCategory; title: string; content: string }): Promise<Post> => {
  const { data } = await api.post('/board/posts', body)
  return data
}
