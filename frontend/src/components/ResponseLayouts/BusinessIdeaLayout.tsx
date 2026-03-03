import { motion } from 'framer-motion'
import { MapPin, TrendingUp, Clock, AlertTriangle, Landmark, ArrowRight, CheckCircle2 } from 'lucide-react'
import { BusinessIdeaData } from '@/types'

interface Props { data: BusinessIdeaData; onStartJourney?: () => void }
const fmt = (n: number) => `K${n.toLocaleString()}`

export default function BusinessIdeaLayout({ data, onStartJourney }: Props) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="w-full max-w-2xl">

      {/* Header — navy with cornflower accent */}
      <div className="relative overflow-hidden rounded-2xl shadow-navy mb-3" style={{ background: 'linear-gradient(135deg, #0A1628 0%, #0D1F3C 60%, #162B4D 100%)' }}>
        <div className="absolute inset-0 neural-overlay pointer-events-none" />
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-cornflower-gradient" />
        <div className="relative p-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-kip-cornflower/20 border border-kip-cornflower/40 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-kip-cornflower animate-pulse-slow" />
            <span className="text-kip-cornflower text-xs font-mono font-semibold tracking-widest uppercase">Business Opportunity</span>
          </div>
          <h2 className="font-display font-bold text-3xl text-white mb-2 leading-tight">{data.title}</h2>
          <p className="text-white/60 font-body text-base italic">{data.tagline}</p>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        {[
          { label: 'Startup Capital', value: `${fmt(data.startup_capital_min)} – ${fmt(data.startup_capital_max)}`, accent: true },
          { label: 'Monthly Revenue', value: `${fmt(data.monthly_revenue_min)} – ${fmt(data.monthly_revenue_max)}` },
          { label: 'Break-even', value: `~${data.breakeven_months} months` },
        ].map((m, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.08 }}
            className={`rounded-xl p-3 border ${m.accent ? 'bg-kip-cornflower/10 border-kip-cornflower/40' : 'bg-white border-kip-light'}`}>
            <p className={`text-xs font-body font-medium mb-1 ${m.accent ? 'text-kip-cornflower' : 'text-kip-muted'}`}>{m.label}</p>
            <p className={`font-mono font-bold text-sm ${m.accent ? 'text-kip-cornflower' : 'text-kip-charcoal'}`}>{m.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Location */}
      <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-kip-navymid/8 border border-kip-navymid/15 mb-3">
        <MapPin size={14} className="text-kip-cornflower shrink-0" />
        <span className="text-sm font-body text-kip-muted">
          <span className="font-semibold text-kip-charcoal">Best locations: </span>
          {data.best_for_location.join(' · ')}
        </span>
      </div>

      {/* Why Zambia */}
      <div className="bg-white rounded-xl border border-kip-light p-4 mb-3">
        <h3 className="font-body font-semibold text-kip-charcoal text-xs mb-2 uppercase tracking-wide">Why This Works in Zambia</h3>
        <p className="text-kip-charcoal/80 text-sm font-body leading-relaxed">{data.why_zambia}</p>
      </div>

      {/* Steps */}
      <div className="bg-white rounded-xl border border-kip-light p-4 mb-3">
        <h3 className="font-body font-semibold text-kip-charcoal text-xs mb-3 uppercase tracking-wide">Your First Steps</h3>
        <div className="space-y-2">
          {data.first_steps.map((step, i) => (
            <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 + i * 0.07 }} className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-kip-cornflower/15 flex items-center justify-center mt-0.5">
                <span className="text-kip-cornflower font-mono text-xs font-bold">{step.step}</span>
              </div>
              <div className="flex-1">
                <span className="text-sm font-body font-medium text-kip-charcoal">{step.action}</span>
                <span className="text-xs text-kip-muted font-mono ml-2">{step.cost} · {step.timeframe}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Risk + Funding */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="bg-red-50 border border-red-100 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1.5">
            <AlertTriangle size={13} className="text-red-500" />
            <span className="text-xs font-body font-semibold text-red-600 uppercase tracking-wide">Main Risk</span>
          </div>
          <p className="text-sm font-body text-red-700/80 leading-snug">{data.main_risk}</p>
        </div>
        <div className="bg-kip-cornflowerfaint border border-kip-cornflower/25 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1.5">
            <Landmark size={13} className="text-kip-cornflower" />
            <span className="text-xs font-body font-semibold text-kip-cornflowerdark uppercase tracking-wide">Funding</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {data.funding_options.map((f, i) => (
              <span key={i} className="text-xs bg-kip-cornflower/15 text-kip-cornflowerdark px-2 py-0.5 rounded-full font-body font-medium">{f}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Verdict */}
      <div className="border-l-2 border-kip-cornflower pl-4 mb-4">
        <p className="text-sm font-body italic text-kip-muted">
          <span className="font-semibold text-kip-charcoal not-italic">KIP: </span>{data.kip_verdict}
        </p>
      </div>

      {/* CTA */}
      {onStartJourney && (
        <motion.button
          initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}
          onClick={onStartJourney} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
          className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl
                     bg-kip-cornflower text-white font-body font-semibold text-sm
                     hover:bg-kip-cornflowerdark transition-colors shadow-glow group"
        >
          Start this Business Journey with KIP
          <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
        </motion.button>
      )}
    </motion.div>
  )
}
