import { NavLink } from 'react-router-dom'
import { LayoutDashboard, SearchCode, History, Lightbulb, Database, Table2 } from 'lucide-react'

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/analyzer', label: 'Query Analyzer', icon: SearchCode },
  { to: '/history', label: 'Query History', icon: History },
  { to: '/recommendations', label: 'Index Recommendations', icon: Lightbulb },
  { to: '/explorer', label: 'Database Explorer', icon: Table2 },
]

export default function Sidebar() {
  return (
    <aside className="hidden md:flex md:flex-col w-64 shrink-0 bg-slate-900 text-slate-200 min-h-screen">
      <div className="flex items-center gap-2 px-6 py-5 border-b border-slate-800">
        <Database className="w-6 h-6 text-brand-400" />
        <div>
          <p className="font-semibold text-white leading-tight">QueryWise</p>
          <p className="text-xs text-slate-400 leading-tight">Query Optimizer</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-slate-800 text-xs text-slate-500">
        Safe by design: read-only SELECT queries only. No index is ever
        created automatically.
      </div>
    </aside>
  )
}
