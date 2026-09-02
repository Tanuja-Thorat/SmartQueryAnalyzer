import { Loader2, Inbox, AlertTriangle } from 'lucide-react'

export function LoadingSpinner({ label = 'Loading…' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-slate-500">
      <Loader2 className="w-6 h-6 animate-spin mb-2 text-brand-600" />
      <p className="text-sm">{label}</p>
    </div>
  )
}

export function EmptyState({ title = 'Nothing here yet', description, icon: Icon = Inbox }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center text-slate-500">
      <div className="p-3 bg-slate-100 rounded-full mb-3">
        <Icon className="w-6 h-6 text-slate-400" />
      </div>
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {description && <p className="text-xs text-slate-400 mt-1 max-w-sm">{description}</p>}
    </div>
  )
}

export function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
      <span>{message}</span>
    </div>
  )
}
