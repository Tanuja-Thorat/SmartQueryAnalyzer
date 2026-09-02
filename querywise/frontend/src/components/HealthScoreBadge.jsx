const STATUS_STYLES = {
  Excellent: 'bg-emerald-100 text-emerald-700 ring-emerald-200',
  Good: 'bg-blue-100 text-blue-700 ring-blue-200',
  'Needs Improvement': 'bg-amber-100 text-amber-700 ring-amber-200',
  Poor: 'bg-red-100 text-red-700 ring-red-200',
}

const RING_COLOR = {
  Excellent: '#10b981',
  Good: '#2563eb',
  'Needs Improvement': '#f59e0b',
  Poor: '#ef4444',
}

export default function HealthScoreBadge({ score, status, size = 'md' }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.Good
  const ringColor = RING_COLOR[status] || RING_COLOR.Good
  const dim = size === 'lg' ? 96 : 56
  const stroke = size === 'lg' ? 8 : 6
  const radius = (dim - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const progress = Math.max(0, Math.min(100, score)) / 100
  const dashOffset = circumference * (1 - progress)

  return (
    <div className="flex items-center gap-3">
      <svg width={dim} height={dim} className="shrink-0">
        <g transform={`rotate(-90 ${dim / 2} ${dim / 2})`}>
          <circle cx={dim / 2} cy={dim / 2} r={radius} stroke="#e2e8f0" strokeWidth={stroke} fill="none" />
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            stroke={ringColor}
            strokeWidth={stroke}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
          />
        </g>
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="middle"
          style={{ fill: '#0f172a', fontWeight: 700, fontSize: size === 'lg' ? 20 : 14 }}
        >
          {score}
        </text>
      </svg>
      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ${style}`}>
        {status}
      </span>
    </div>
  )
}
