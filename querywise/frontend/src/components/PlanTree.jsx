import { CheckCircle2, AlertTriangle, AlertOctagon } from 'lucide-react'

const WARNING_STYLES = {
  good: {
    border: 'border-emerald-200',
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    icon: CheckCircle2,
  },
  warning: {
    border: 'border-amber-200',
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    icon: AlertTriangle,
  },
  critical: {
    border: 'border-red-200',
    bg: 'bg-red-50',
    text: 'text-red-700',
    icon: AlertOctagon,
  },
}

function PlanNode({ node, depth = 0 }) {
  const style = WARNING_STYLES[node.warning_level] || WARNING_STYLES.good
  const Icon = style.icon

  return (
    <div className="relative">
      <div className={`flex items-start gap-3 rounded-lg border ${style.border} ${style.bg} px-4 py-3`}>
        <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${style.text}`} />
        <div className="min-w-0">
          <p className={`text-sm font-semibold ${style.text}`}>{node.operation}</p>
          {node.detail && (
            <p className="text-xs text-slate-500 mt-0.5 break-words code-font">{node.detail}</p>
          )}
          <div className="flex gap-4 mt-1.5 text-xs text-slate-500">
            <span>Cost: <span className="font-medium text-slate-700">{node.cost}</span></span>
            <span>Rows: <span className="font-medium text-slate-700">{node.rows}</span></span>
          </div>
        </div>
      </div>

      {node.children && node.children.length > 0 && (
        <div className="ml-6 mt-2 pl-4 border-l-2 border-dashed border-slate-200 space-y-2">
          {node.children.map((child, idx) => (
            <PlanNode key={idx} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function PlanTree({ plan }) {
  if (!plan) return null
  return (
    <div className="space-y-2">
      <PlanNode node={plan} />
    </div>
  )
}
