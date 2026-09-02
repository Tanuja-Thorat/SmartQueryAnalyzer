import { useEffect, useState } from 'react'
import { Copy, Check, Lightbulb } from 'lucide-react'
import { getRecommendations } from '../services/api.js'
import Card from '../components/Card.jsx'
import { LoadingSpinner, EmptyState, ErrorBanner } from '../components/Feedback.jsx'

export default function IndexRecommendations() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(null)

  useEffect(() => {
    load()
  }, [])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const data = await getRecommendations()
      setItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleCopy(text, key) {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 1500)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Index Recommendations</h1>
        <p className="text-sm text-slate-500 mt-1">
          Every recommendation QueryWise has generated across all analyzed queries. Review and apply manually —
          nothing here is executed automatically.
        </p>
      </div>

      <ErrorBanner message={error} />

      {loading ? (
        <LoadingSpinner label="Loading recommendations…" />
      ) : items.length === 0 ? (
        <Card>
          <EmptyState
            title="No index recommendations yet"
            description="Analyze a query with a sequential scan or missing index to generate recommendations here."
            icon={Lightbulb}
          />
        </Card>
      ) : (
        <div className="space-y-4">
          {items.map((rec) => {
            const key = `rec-${rec.id}`
            return (
              <Card key={rec.id}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-800">
                      Table: <span className="code-font">{rec.table}</span>
                    </p>
                    <p className="text-xs text-slate-500 mt-1 max-w-xl">{rec.reason}</p>
                    <p className="code-font text-xs text-slate-400 mt-2 truncate max-w-xl">{rec.query_text}</p>
                  </div>
                  <span className="shrink-0 text-xs font-semibold bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full">
                    ~{rec.estimated_improvement}% faster (est.)
                  </span>
                </div>

                <div className="relative mt-3">
                  <pre className="code-font text-xs bg-slate-900 text-slate-100 rounded-lg p-3 overflow-x-auto">
{rec.index_sql}
                  </pre>
                  <button
                    onClick={() => handleCopy(rec.index_sql, key)}
                    className="absolute top-2 right-2 text-slate-300 hover:text-white"
                    title="Copy SQL"
                  >
                    {copied === key ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>

                <p className="text-[11px] text-slate-400 mt-2">
                  Generated {new Date(rec.created_at).toLocaleString()}
                </p>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
