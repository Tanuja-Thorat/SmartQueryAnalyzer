import { useState, useRef } from 'react'
import { Play, Wand2, Copy, Check, FlaskConical, ListChecks, ChevronDown } from 'lucide-react'
import { analyzeQuery, simulateIndex } from '../services/api.js'
import Card from '../components/Card.jsx'
import { LoadingSpinner, ErrorBanner, EmptyState } from '../components/Feedback.jsx'
import HealthScoreBadge from '../components/HealthScoreBadge.jsx'
import PlanTree from '../components/PlanTree.jsx'

// 15 example queries covering every major case QueryWise is built to
// demonstrate, all matched against the 12-table demo schema (see
// database/schema.sql). Grouped loosely by what each one showcases.
const EXAMPLE_QUERIES = [
  {
    label: 'Sequential scan (unindexed FK)',
    sql: 'SELECT * FROM employees WHERE department_id = 3;',
  },
  {
    label: 'Salary filtering (unindexed column)',
    sql: 'SELECT * FROM employees WHERE salary > 80000;',
  },
  {
    label: 'Customer city filter (unindexed)',
    sql: "SELECT * FROM customers WHERE city = 'Pune';",
  },
  {
    label: 'Single JOIN with WHERE',
    sql: `SELECT o.id, c.first_name, c.last_name, o.total_amount
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'completed';`,
  },
  {
    label: 'Multi-table JOIN (4 tables)',
    sql: `SELECT o.id, c.first_name, p.name, oi.quantity
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id;`,
  },
  {
    label: 'LEFT JOIN — orders without shipments',
    sql: `SELECT o.id, o.status, s.status AS shipment_status
FROM orders o
LEFT JOIN shipments s ON o.id = s.order_id
WHERE s.id IS NULL;`,
  },
  {
    label: 'ORDER BY on unindexed column',
    sql: `SELECT * FROM products
WHERE price > 500
ORDER BY price DESC;`,
  },
  {
    label: 'GROUP BY with COUNT',
    sql: `SELECT category_id, COUNT(*)
FROM products
GROUP BY category_id;`,
  },
  {
    label: 'GROUP BY with SUM + ORDER BY',
    sql: `SELECT customer_id, SUM(total_amount)
FROM orders
GROUP BY customer_id
ORDER BY SUM(total_amount) DESC;`,
  },
  {
    label: 'AVG aggregate',
    sql: `SELECT category_id, AVG(price)
FROM products
GROUP BY category_id;`,
  },
  {
    label: 'Date range filter (unindexed)',
    sql: `SELECT *
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days';`,
  },
  {
    label: 'Multiple WHERE conditions',
    sql: `SELECT *
FROM products
WHERE price BETWEEN 500 AND 2000
AND category_id = 3;`,
  },
  {
    label: 'JOIN + GROUP BY (reviews per product)',
    sql: `SELECT p.name, COUNT(r.id) AS review_count, AVG(r.rating) AS avg_rating
FROM products p
JOIN reviews r ON p.id = r.product_id
GROUP BY p.name
ORDER BY review_count DESC;`,
  },
  {
    label: 'Payments joined to orders',
    sql: `SELECT pay.id, o.status, pay.amount, pay.payment_method
FROM payments pay
JOIN orders o ON pay.order_id = o.id
WHERE pay.status = 'completed';`,
  },
  {
    label: 'Customer address lookup (indexed FK)',
    sql: `SELECT c.first_name, c.last_name, a.city, a.postal_code
FROM customers c
JOIN addresses a ON c.id = a.customer_id
WHERE a.is_default = true;`,
  },
]

export default function QueryAnalyzer() {
  const [query, setQuery] = useState(EXAMPLE_QUERIES[0].sql)
  const [runAnalyze, setRunAnalyze] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [copied, setCopied] = useState(null)
  const [simState, setSimState] = useState({}) // { [index]: {loading, data, error} }
  const [showExamples, setShowExamples] = useState(false)
  const editorRef = useRef(null)

  function loadExample(sql) {
    setQuery(sql)
    setShowExamples(false)
    editorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  async function handleAnalyze() {
    setLoading(true)
    setError('')
    setResult(null)
    setSimState({})
    try {
      const data = await analyzeQuery(query, runAnalyze)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSimulate(rec, idx) {
    setSimState((s) => ({ ...s, [idx]: { loading: true } }))
    try {
      const data = await simulateIndex(query, rec.index_sql)
      setSimState((s) => ({ ...s, [idx]: { loading: false, data } }))
    } catch (err) {
      setSimState((s) => ({ ...s, [idx]: { loading: false, error: err.message } }))
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
        <h1 className="text-xl font-bold text-slate-900">Query Analyzer</h1>
        <p className="text-sm text-slate-500 mt-1">
          Paste a read-only SELECT query to get a health score, plan breakdown, and index recommendations.
        </p>
      </div>

      <Card>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setShowExamples((s) => !s)}
              className="inline-flex items-center gap-2 text-sm font-medium text-brand-700 hover:text-brand-800"
            >
              <ListChecks className="w-4 h-4" />
              Example Queries
              <ChevronDown className={`w-4 h-4 transition-transform ${showExamples ? 'rotate-180' : ''}`} />
            </button>
            <span className="text-xs text-slate-400">{EXAMPLE_QUERIES.length} examples across the demo schema</span>
          </div>

          {showExamples && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 border border-slate-200 rounded-lg p-3 bg-slate-50">
              {EXAMPLE_QUERIES.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => loadExample(ex.sql)}
                  className="text-left px-3 py-2 rounded-lg bg-white border border-slate-200 hover:border-brand-400 hover:shadow-sm transition-all"
                >
                  <p className="text-xs font-medium text-slate-700">{ex.label}</p>
                  <p className="code-font text-[11px] text-slate-400 truncate mt-0.5">{ex.sql.split('\n')[0]}</p>
                </button>
              ))}
            </div>
          )}

          <textarea
            ref={editorRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={7}
            spellCheck={false}
            placeholder="SELECT * FROM your_table WHERE ..."
            className="w-full rounded-lg border border-slate-300 code-font text-sm p-4 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-y"
          />

          <div className="flex flex-wrap items-center justify-end gap-3">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-xs text-slate-500 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={runAnalyze}
                  onChange={(e) => setRunAnalyze(e.target.checked)}
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                Run EXPLAIN ANALYZE (actually executes the query)
              </label>
              <button
                onClick={handleAnalyze}
                disabled={loading || !query.trim()}
                className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                <Play className="w-4 h-4" />
                {loading ? 'Analyzing…' : 'Analyze Query'}
              </button>
            </div>
          </div>
        </div>
      </Card>

      <ErrorBanner message={error} />

      {loading && <LoadingSpinner label="Running EXPLAIN and analyzing the plan…" />}

      {!loading && !result && !error && (
        <Card>
          <EmptyState
            title="Run an analysis to see results"
            description="Your query health score, execution plan, and index recommendations will appear here."
            icon={FlaskConical}
          />
        </Card>
      )}

      {result && (
        <div className="space-y-6">
          {/* Health score + summary */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card title="Query Health Score" className="lg:col-span-1">
              <div className="flex flex-col items-center py-2">
                <HealthScoreBadge score={result.health_score} status={result.health_status} size="lg" />
                {result.is_slow && (
                  <p className="mt-3 text-xs font-medium text-red-600 bg-red-50 px-3 py-1 rounded-full">
                    Slow query detected
                  </p>
                )}
              </div>
            </Card>

            <Card title="Execution Plan Summary" className="lg:col-span-2">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                <SummaryStat label="Total Cost" value={result.total_cost} />
                <SummaryStat label="Startup Cost" value={result.startup_cost} />
                <SummaryStat label="Estimated Rows" value={result.estimated_rows} />
                <SummaryStat label="Actual Rows" value={result.actual_rows ?? '—'} />
                <SummaryStat
                  label="Execution Time"
                  value={result.execution_time != null ? `${result.execution_time.toFixed?.(1) ?? result.execution_time} ms` : '—'}
                />
                <SummaryStat label="Primary Scan Type" value={result.scan_type ?? '—'} />
              </div>
            </Card>
          </div>

          {/* AI Explanation */}
          {result.ai_explanation && (
            <Card title="AI Explanation" subtitle="Generated by OpenRouter">
              <div className="prose prose-sm max-w-none text-slate-700">
                <p className="whitespace-pre-wrap">{result.ai_explanation}</p>
              </div>
            </Card>
          )}

          {/* Issues */}
          <Card title="Performance Issues Detected">
            <ul className="space-y-2">
              {result.issues.map((issue, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
                  {issue}
                </li>
              ))}
            </ul>
          </Card>

          {/* Plan tree */}
          <Card title="Execution Plan" subtitle="Simplified visualization of the query plan tree">
            <PlanTree plan={result.plan_tree} />
          </Card>

          {/* Index recommendations */}
          <Card title="Index Recommendations" subtitle="Never executed automatically — review and apply manually">
            {result.recommendations.length === 0 ? (
              <EmptyState
                title="No index recommendations"
                description="QueryWise didn't find a clear missing-index opportunity for this query."
                icon={Wand2}
              />
            ) : (
              <div className="space-y-4">
                {result.recommendations.map((rec, idx) => {
                  const sim = simState[idx]
                  const copyKey = `rec-${idx}`
                  return (
                    <div key={idx} className="border border-slate-200 rounded-lg p-4 space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-slate-800">
                            Table: <span className="code-font">{rec.table}</span>
                          </p>
                          <p className="text-xs text-slate-500 mt-1">{rec.reason}</p>
                        </div>
                        <span className="shrink-0 text-xs font-semibold bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full">
                          ~{rec.estimated_improvement}% faster (est.)
                        </span>
                      </div>

                      <div className="relative">
                        <pre className="code-font text-xs bg-slate-900 text-slate-100 rounded-lg p-3 overflow-x-auto">
{rec.index_sql}
                        </pre>
                        <button
                          onClick={() => handleCopy(rec.index_sql, copyKey)}
                          className="absolute top-2 right-2 text-slate-300 hover:text-white"
                          title="Copy SQL"
                        >
                          {copied === copyKey ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                        </button>
                      </div>

                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => handleSimulate(rec, idx)}
                          disabled={sim?.loading}
                          className="inline-flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                        >
                          <FlaskConical className="w-3.5 h-3.5" />
                          {sim?.loading ? 'Simulating…' : 'Run What-If Simulation'}
                        </button>
                        <span className="text-[11px] text-slate-400">
                          Simulation only — no index is created in your database.
                        </span>
                      </div>

                      {sim?.error && <ErrorBanner message={sim.error} />}
                      {sim?.data && (
                        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm">
                          <div className="flex flex-wrap gap-x-8 gap-y-2">
                            <div>
                              <p className="text-xs text-slate-500">Original Cost</p>
                              <p className="font-semibold text-slate-800">{sim.data.original_cost}</p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500">Estimated Optimized Cost</p>
                              <p className="font-semibold text-emerald-700">{sim.data.estimated_optimized_cost}</p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500">Estimated Improvement</p>
                              <p className="font-semibold text-emerald-700">{sim.data.estimated_improvement_percent}%</p>
                            </div>
                          </div>
                          <p className="text-[11px] text-slate-500 mt-2">{sim.data.note}</p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}

function SummaryStat({ label, value }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-semibold text-slate-800 mt-0.5">{value}</p>
    </div>
  )
}
