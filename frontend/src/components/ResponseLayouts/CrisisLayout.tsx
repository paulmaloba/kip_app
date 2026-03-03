import { motion } from 'framer-motion'
import { AlertCircle, Square, XCircle, Phone } from 'lucide-react'
import { CrisisData } from '@/types'

interface Props { data: CrisisData }
const sev = {
  high:   { color:'text-red-600', bg:'bg-red-50', border:'border-red-200', bar:'bg-red-500', label:'HIGH SEVERITY' },
  medium: { color:'text-amber-600', bg:'bg-amber-50', border:'border-amber-200', bar:'bg-amber-500', label:'MODERATE SEVERITY' },
  low:    { color:'text-status-up', bg:'bg-green-50', border:'border-green-200', bar:'bg-status-up', label:'LOW SEVERITY' },
}
export default function CrisisLayout({ data }: Props) {
  const cfg = sev[data.severity] || sev.medium
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-2xl">
      <div className={`rounded-2xl ${cfg.bg} border ${cfg.border} overflow-hidden mb-3`}>
        <div className={`h-1.5 w-full ${cfg.bar}`} />
        <div className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle size={22} className={cfg.color} />
            <span className={`text-xs font-mono font-bold tracking-widest ${cfg.color}`}>CRISIS RESPONSE · {cfg.label}</span>
          </div>
          <p className="font-body text-sm text-gray-700 leading-relaxed">
            <span className="font-semibold text-gray-900">Situation: </span>{data.situation_assessment}
          </p>
        </div>
      </div>

      <div className="bg-white border border-kip-light rounded-xl p-4 mb-3">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <h3 className="font-body font-bold text-sm text-kip-charcoal uppercase tracking-wide">Do This Now — Next 48 Hours</h3>
        </div>
        {data.do_now.map((step, i) => (
          <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 + i * 0.08 }} className="flex items-start gap-3 mb-2.5">
            <Square size={16} className="text-red-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-body font-semibold text-kip-charcoal">{step.action}</p>
              {step.why && <p className="text-xs text-kip-muted italic mt-0.5">{step.why}</p>}
            </div>
          </motion.div>
        ))}
      </div>

      <div className="bg-white border border-kip-light rounded-xl p-4 mb-3">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 rounded-full bg-amber-400" />
          <h3 className="font-body font-bold text-sm text-kip-charcoal uppercase tracking-wide">Do This Week</h3>
        </div>
        {data.do_this_week.map((step, i) => (
          <div key={i} className="flex items-start gap-3 mb-2">
            <Square size={16} className="text-amber-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-body text-kip-charcoal">{step.action}</p>
              {step.why && <p className="text-xs text-kip-muted italic mt-0.5">{step.why}</p>}
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-kip-light border border-kip-light rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-2"><XCircle size={13} className="text-red-500" /><span className="text-xs font-body font-bold uppercase tracking-wide text-red-600">Don't Do This</span></div>
          <p className="text-sm font-body text-kip-charcoal">{data.avoid_this_mistake}</p>
        </div>
        <div className="bg-kip-cornflowerfaint border border-kip-cornflower/25 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-2"><Phone size={13} className="text-kip-cornflower" /><span className="text-xs font-body font-bold uppercase tracking-wide text-kip-cornflowerdark">Who Can Help</span></div>
          {data.who_can_help.map((h, i) => <p key={i} className="text-xs font-body text-kip-charcoal">{h}</p>)}
        </div>
      </div>

      <div className="border-l-2 border-kip-cornflower pl-4">
        <p className="text-sm font-body text-kip-muted italic">
          <span className="font-semibold text-kip-charcoal not-italic">Outlook: </span>{data.honest_outlook}
        </p>
      </div>
    </motion.div>
  )
}
