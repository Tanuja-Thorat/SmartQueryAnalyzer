export default function Card({ title, subtitle, children, className = '', actions }) {
  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div>
            {title && <h3 className="text-sm font-semibold text-slate-800">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
          {actions}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  )
}

export function StatCard({ label, value, hint, icon: Icon, tone = 'default' }) {
  const tones = {
    default: 'bg-brand-50 text-brand-700',
    danger: 'bg-red-50 text-red-700',
    success: 'bg-emerald-50 text-emerald-700',
    warning: 'bg-amber-50 text-amber-700',
  }
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex items-start justify-between">
      <div>
        <p className="text-xs font-medium text-slate-500">{label}</p>
        <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
        {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
      </div>
      {Icon && (
        <div className={`p-2.5 rounded-lg ${tones[tone]}`}>
          <Icon className="w-5 h-5" />
        </div>
      )}
    </div>
  )
}
