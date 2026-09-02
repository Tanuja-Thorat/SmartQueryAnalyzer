import { useEffect, useState } from 'react'
import { Table2, KeyRound, Link2, ListTree } from 'lucide-react'
import { getExplorerTables, getExplorerTableDetail } from '../services/api.js'
import Card, { StatCard } from '../components/Card.jsx'
import { LoadingSpinner, EmptyState, ErrorBanner } from '../components/Feedback.jsx'

export default function DatabaseExplorer() {
  const [tables, setTables] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')

  useEffect(() => {
    loadTables()
  }, [])

  async function loadTables() {
    setLoading(true)
    setError('')
    try {
      const data = await getExplorerTables()
      setTables(data.tables)
      if (data.tables.length > 0) {
        selectTable(data.tables[0].table_name)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function selectTable(tableName) {
    setSelected(tableName)
    setDetail(null)
    setDetailError('')
    setDetailLoading(true)
    try {
      const data = await getExplorerTableDetail(tableName)
      setDetail(data)
    } catch (err) {
      setDetailError(err.message)
    } finally {
      setDetailLoading(false)
    }
  }

  const totalRows = tables.reduce((sum, t) => sum + t.row_count, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Database Explorer</h1>
        <p className="text-sm text-slate-500 mt-1">
          A live look at the real PostgreSQL database QueryWise is analyzing — not hardcoded metadata.
        </p>
      </div>

      <ErrorBanner message={error} />

      {loading ? (
        <LoadingSpinner label="Reading database structure…" />
      ) : tables.length === 0 ? (
        <Card>
          <EmptyState
            title="No tables found"
            description="Make sure the target database is running and seeded (see README)."
            icon={Table2}
          />
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <StatCard label="Total Tables" value={tables.length} icon={Table2} />
            <StatCard label="Total Rows (all tables)" value={totalRows.toLocaleString()} icon={ListTree} tone="success" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card title="Tables" className="lg:col-span-1">
              <div className="space-y-1 max-h-[520px] overflow-y-auto">
                {tables.map((t) => (
                  <button
                    key={t.table_name}
                    onClick={() => selectTable(t.table_name)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left text-sm transition-colors ${
                      selected === t.table_name
                        ? 'bg-brand-600 text-white'
                        : 'text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    <span className="code-font truncate">{t.table_name}</span>
                    <span className={`text-xs shrink-0 ml-2 ${selected === t.table_name ? 'text-brand-100' : 'text-slate-400'}`}>
                      {t.row_count.toLocaleString()} rows
                    </span>
                  </button>
                ))}
              </div>
            </Card>

            <div className="lg:col-span-2 space-y-6">
              <ErrorBanner message={detailError} />
              {detailLoading && <LoadingSpinner label="Loading table detail…" />}

              {detail && !detailLoading && (
                <>
                  <Card title={`Table: ${detail.table_name}`} subtitle={`${detail.row_count.toLocaleString()} rows`}>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
                            <th className="py-2 pr-4 font-medium">Column</th>
                            <th className="py-2 pr-4 font-medium">Type</th>
                            <th className="py-2 pr-4 font-medium">Nullable</th>
                            <th className="py-2 font-medium">Key</th>
                          </tr>
                        </thead>
                        <tbody>
                          {detail.columns.map((col) => {
                            const isPk = detail.primary_keys.includes(col.column_name)
                            const fk = detail.foreign_keys.find((f) => f.column_name === col.column_name)
                            return (
                              <tr key={col.column_name} className="border-b border-slate-100 last:border-0">
                                <td className="py-2 pr-4 code-font text-slate-700">{col.column_name}</td>
                                <td className="py-2 pr-4 text-slate-500">{col.data_type}</td>
                                <td className="py-2 pr-4 text-slate-500">{col.is_nullable === 'YES' ? 'Yes' : 'No'}</td>
                                <td className="py-2">
                                  {isPk && (
                                    <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full mr-1">
                                      <KeyRound className="w-3 h-3" /> PK
                                    </span>
                                  )}
                                  {fk && (
                                    <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full">
                                      <Link2 className="w-3 h-3" /> → {fk.referenced_table}.{fk.referenced_column}
                                    </span>
                                  )}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </Card>

                  <Card title="Existing Indexes" subtitle="Straight from pg_indexes">
                    {detail.indexes.length === 0 ? (
                      <p className="text-sm text-slate-500">No indexes on this table besides the implicit primary key.</p>
                    ) : (
                      <div className="space-y-2">
                        {detail.indexes.map((idx) => (
                          <pre key={idx.indexname} className="code-font text-xs bg-slate-900 text-slate-100 rounded-lg p-3 overflow-x-auto">
{idx.indexdef}
                          </pre>
                        ))}
                      </div>
                    )}
                  </Card>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
