import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, History as HistoryIcon } from 'lucide-react'
import { getHistory } from '../services/api.js'
import Card from '../components/Card.jsx'
import { LoadingSpinner, EmptyState, ErrorBanner } from '../components/Feedback.jsx'

export default function QueryHistory() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [slowOnly, setSlowOnly] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const timer = setTimeout(load, 300) // debounce search typing
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, slowOnly])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const data = await getHistory({ search, slowOnly })
      setItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Query History</h1>
        <p className="text-sm text-slate-500 mt-1">Every analysis you've run, searchable and filterable.</p>
      </div>

      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search query text…"
              className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={slowOnly}
              onChange={(e) => setSlowOnly(e.target.checked)}
              className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            />
            Slow queries only
          </label>
        </div>
      </Card>

      <ErrorBanner message={error} />

      <Card>
        {loading ? (
          <LoadingSpinner label="Loading history…" />
        ) : items.length === 0 ? (
          <EmptyState
            title="No query history yet"
            description="Analyzed queries will show up here."
            icon={HistoryIcon}
          />
        ) : (
          <div className="overflow-x-auto -mx-5">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
                  <th className="px-5 py-2 font-medium">Query</th>
                  <th className="px-5 py-2 font-medium">Cost</th>
                  <th className="px-5 py-2 font-medium">Exec Time</th>
                  <th className="px-5 py-2 font-medium">Health</th>
                  <th className="px-5 py-2 font-medium">Slow?</th>
                  <th className="px-5 py-2 font-medium">Indexes</th>
                  <th className="px-5 py-2 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr
                    key={row.analysis_id}
                    onClick={() => navigate(`/history/${row.analysis_id}`)}
                    className="border-b border-slate-100 last:border-0 hover:bg-slate-50 cursor-pointer"
                  >
                    <td className="px-5 py-3 max-w-xs">
                      <p className="code-font text-xs text-slate-700 truncate">{row.query_text}</p>
                    </td>
                    <td className="px-5 py-3 text-slate-600">{row.total_cost}</td>
                    <td className="px-5 py-3 text-slate-600">
                      {row.execution_time != null ? `${row.execution_time.toFixed?.(1) ?? row.execution_time} ms` : '—'}
                    </td>
                    <td className="px-5 py-3">
                      <span className="font-medium text-slate-700">{row.health_score}</span>
                      <span className="text-xs text-slate-400"> /100</span>
                    </td>
                    <td className="px-5 py-3">
                      {row.is_slow ? (
                        <span className="text-xs font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded-full">Slow</span>
                      ) : (
                        <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">Normal</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-slate-600">{row.recommendation_count}</td>
                    <td className="px-5 py-3 text-slate-500 text-xs whitespace-nowrap">
                      {new Date(row.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
