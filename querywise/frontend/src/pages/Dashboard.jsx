import { useEffect, useState } from 'react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { Database, AlertTriangle, Gauge, Activity, Lightbulb, Table2 } from 'lucide-react'
import { getDashboard } from '../services/api.js'
import { StatCard } from '../components/Card.jsx'
import Card from '../components/Card.jsx'
import { LoadingSpinner, EmptyState, ErrorBanner } from '../components/Feedback.jsx'

const PIE_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899']

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    load()
  }, [])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const result = await getDashboard()
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <LoadingSpinner label="Loading dashboard…" />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          Overall database query performance at a glance.
        </p>
      </div>

      <ErrorBanner message={error} />

      {data && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
            <StatCard
              label="Total Tables"
              value={data.summary.total_tables}
              icon={Table2}
            />
            <StatCard
              label="Total Queries Analyzed"
              value={data.summary.total_queries_analyzed}
              icon={Database}
            />
            <StatCard
              label="Slow Queries"
              value={data.summary.slow_queries}
              icon={AlertTriangle}
              tone="danger"
            />
            <StatCard
              label="Avg Query Cost"
              value={data.summary.average_query_cost}
              icon={Activity}
            />
            <StatCard
              label="Avg Health Score"
              value={`${data.summary.average_health_score}/100`}
              icon={Gauge}
              tone="success"
            />
            <StatCard
              label="Recommended Indexes"
              value={data.summary.recommended_indexes}
              icon={Lightbulb}
              tone="warning"
            />
          </div>

          {data.summary.total_queries_analyzed === 0 ? (
            <Card>
              <EmptyState
                title="No queries analyzed yet"
                description="Head to the Query Analyzer to run your first SQL query and see results appear here."
                icon={Database}
              />
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card title="Query Cost Over Time" subtitle="Planner total cost per analyzed query">
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={data.trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="cost" stroke="#3b82f6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </Card>

              <Card title="Health Score Trend" subtitle="0–100 score per analyzed query">
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={data.trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="health_score" stroke="#10b981" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </Card>

              <Card title="Execution Time Over Time" subtitle="Milliseconds (EXPLAIN ANALYZE runs only)">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={data.trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="execution_time" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              <Card title="Query Scan Types" subtitle="Distribution of primary scan operation used">
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie
                      data={data.scan_types}
                      dataKey="count"
                      nameKey="scan_type"
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      label={({ scan_type, count }) => `${scan_type}: ${count}`}
                    >
                      {data.scan_types.map((entry, idx) => (
                        <Cell key={entry.scan_type} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Card>

              {data.most_frequent_tables.length > 0 && (
                <Card
                  title="Most Frequently Analyzed Tables"
                  subtitle="Which tables you've been analyzing the most"
                  className="lg:col-span-2"
                >
                  <div className="space-y-2">
                    {data.most_frequent_tables.map((t) => {
                      const max = data.most_frequent_tables[0].times_analyzed
                      const pct = Math.round((t.times_analyzed / max) * 100)
                      return (
                        <div key={t.table_name} className="flex items-center gap-3">
                          <span className="code-font text-sm text-slate-700 w-40 shrink-0 truncate">{t.table_name}</span>
                          <div className="flex-1 bg-slate-100 rounded-full h-2.5">
                            <div
                              className="bg-brand-500 h-2.5 rounded-full"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="text-xs text-slate-500 w-16 text-right shrink-0">
                            {t.times_analyzed} {t.times_analyzed === 1 ? 'query' : 'queries'}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </Card>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
