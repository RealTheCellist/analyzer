import { CircularProgressbar, buildStyles } from 'react-circular-progressbar'
import 'react-circular-progressbar/dist/styles.css'
import { Verdict } from '../types'

interface Props {
  score: number
  verdict: Verdict
}

export default function ScoreGauge({ score, verdict }: Props) {
  const colorMap: Record<string, string> = {
    QUALIFIED: '#22c55e',
    WATCHLIST: '#eab308',
    DISQUALIFIED: '#ef4444',
  }
  const color = colorMap[verdict] ?? '#ef4444'

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="w-44 h-44">
        <CircularProgressbar
          value={score}
          maxValue={100}
          text={`${Math.round(score)}`}
          styles={buildStyles({
            textSize: '22px',
            pathColor: color,
            textColor: '#ffffff',
            trailColor: '#1f2937',
            strokeLinecap: 'round',
          })}
        />
      </div>
      <span
        className={`text-sm font-semibold px-3 py-1 rounded-full ${
          verdict === 'QUALIFIED'
            ? 'bg-green-500/20 text-green-400'
            : verdict === 'WATCHLIST'
            ? 'bg-yellow-500/20 text-yellow-400'
            : 'bg-red-500/20 text-red-400'
        }`}
      >
        {verdict === 'QUALIFIED' ? '투자 적격' : verdict === 'WATCHLIST' ? '관망' : '투자 부적격'}
      </span>
    </div>
  )
}
