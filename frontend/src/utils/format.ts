import { Market } from '../types'

export function formatPrice(price: number, market: Market): string {
  if (!price || price <= 0) return '-'
  return market === 'KR'
    ? `₩${price.toLocaleString('ko-KR')}`
    : `$${price.toFixed(2)}`
}

export function formatMarketCap(cap: number, market: Market): string {
  if (!cap || cap <= 0) return '-'
  if (market === 'KR') {
    const jo = cap / 1e12
    if (jo >= 1) return `${jo.toFixed(1)}조`
    return `${(cap / 1e8).toFixed(0)}억`
  }
  const b = cap / 1e9
  if (b >= 1000) return `$${(b / 1000).toFixed(1)}T`
  return `$${b.toFixed(1)}B`
}
