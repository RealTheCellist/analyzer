import { Verdict } from '../types'

interface Props {
  verdict: Verdict
}

export default function VerdictBadge({ verdict }: Props) {
  const styleMap: Record<string, { className: string; label: string }> = {
    STRONG_BUY: {
      className: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40',
      label: '★ 강력매수',
    },
    QUALIFIED: {
      className: 'bg-green-500/20 text-green-400 border border-green-500/40',
      label: '✓ 매수',
    },
    WATCHLIST: {
      className: 'bg-blue-500/20 text-blue-400 border border-blue-500/40',
      label: '◐ 관망',
    },
    DISQUALIFIED: {
      className: 'bg-gray-700 text-gray-400 border border-gray-600',
      label: '✕ 투자부적격',
    },
  }

  const { className, label } = styleMap[verdict] ?? styleMap.DISQUALIFIED

  return (
    <span className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-base font-bold ${className}`}>
      {label}
    </span>
  )
}
