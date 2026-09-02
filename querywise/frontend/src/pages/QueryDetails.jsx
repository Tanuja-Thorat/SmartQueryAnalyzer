import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { getHistoryDetail } from '../services/api.js'
import Card from '../components/Card.jsx'
import { LoadingSpinner, ErrorBanner, EmptyState } from '../components/Feedback.jsx'
import HealthScoreBadge from '../components/HealthScoreBadge.jsx'
import PlanTree from '../components/PlanTree.jsx'
import { Wand2 } from 'lucide-react'

export default function QueryDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const result = await getHistoryDetail(id)
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate('/history')}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800"
      >
        <ArrowLeft className="w-4 h-4" /> Back to history
      </button>

      {loading && <LoadingSpinner label="Loading analysis…" />}
      <ErrorBanner message={error} />

      {data && (
        <div className="space-y-6">
          <Card title={`Analysis #${data.analysis_id}`} subtitle={new Date(data.created_at).toLocaleString()}>
            <pre className="code-font text-xs bg-slate-900 text-slate-100 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
{data.query_text}
            </pre>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card title="Query Health Score" className="lg:col-span-1">
              <div className="flex flex-col items-center py-2">
                <HealthScoreBadge score={data.health_score} status={data.health_status} size="lg" />
                {data.is_slow && (
                  <p className="mt-3 text-xs font-medium text-red-600 bg-red-50 px-3 py-1 rounded-full">
                    Slow query
                  </p>
                )}
              </div>
            </Card>

            <Card title="Execution Plan Summary" className="lg:col-span-2">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                <Stat label="Total Cost" value={data.total_cost} />
                <Stat label="Startup Cost" value={data.startup_cost} />
                <Stat label="Estimated Rows" value={data.estimated_rows} />
                <Stat label="Actual Rows" value={data.actual_rows ?? '—'} />
                <Stat
                  label="Execution Time"
                  value={data.execution_time != null ? `${data.execution_time.toFixed?.(1) ?? data.execution_time} ms` : '—'}
                />
                <Stat label="Scan Type" value={data.scan_type ?? '—'} />
              </div>
            </Card>
          </div>

          <Card title="Performance Issues">
            <ul className="space-y-2">
              {data.issues.map((issue, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
                  {issue}
                </li>
              ))}
            </ul>
          </Card>

          {data.plan_tree && (
            <Card title="Execution Plan">
              <PlanTree plan={data.plan_tree} />
            </Card>
          )}

          <Card title="Index Recommendations">
            {data.recommendations.length === 0 ? (
              <EmptyState title="No index recommendations were generated for this query." icon={Wand2} />
            ) : (
              <div className="space-y-3">
                {data.recommendations.map((rec, idx) => (
                  <div key={idx} className="border border-slate-200 rounded-lg p-4">
                    <p className="text-sm font-semibold text-slate-800">
                      Table: <span className="code-font">{rec.table}</span>
                    </p>
                    <p className="text-xs text-slate-500 mt-1">{rec.reason}</p>
                    <pre className="code-font text-xs bg-slate-900 text-slate-100 rounded-lg p-3 mt-2 overflow-x-auto">
{rec.index_sql}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-semibold text-slate-800 mt-0.5">{value}</p>
    </div>
  )
}
