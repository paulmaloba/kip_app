import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus, BookOpen } from 'lucide-react'
import { EconomicData } from '@/types'

interface Props { data: EconomicData }
export default function EconomicLayout({ data }: Props) {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-2xl">
      <div className="rounded-2xl shadow-navy mb-3 overflow-hidden" style={{ background: 'linear-gradient(135deg, #0A1628 0%, #0D1F3C 100%)' }}>
        <div className="absolute inset-0 neural-overlay pointer-events-none" />
        <div className="relative p-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-kip-cornflower/20 border border-kip-cornflower/30 mb-3">
            <span className="text-kip-cornflower text-xs font-mono font-semibold tracking-widest uppercase">Economic Intelligence</span>
          </div>
          <h2 className="font-display font-bold text-2xl text-white leading-snug">{data.headline}</h2>
        </div>
      </div>

      {data.data_points?.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-3">
          {data.data_points.map((dp, i) => {
            const TIcon = dp.trend === 'up' ? TrendingUp : dp.trend === 'down' ? TrendingDown : Minus
            const tColor = dp.trend === 'up' ? 'text-status-up' : dp.trend === 'down' ? 'text-status-down' : 'text-kip-muted'
            return (
              <motion.div key={i} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 + i * 0.06 }}
                className="bg-white border border-kip-light rounded-xl p-3">
                <p className="text-xs font-body text-kip-muted mb-1 truncate">{dp.label}</p>
                <div className="flex items-center gap-1.5">
                  <span className="font-mono font-bold text-kip-charcoal text-sm">{dp.value}</span>
                  <TIcon size={13} className={tColor} />
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      <div className="bg-white border border-kip-light rounded-xl p-4 mb-3">
        <p className="font-body text-sm text-kip-charcoal/80 leading-relaxed whitespace-pre-wrap">{data.summary}</p>
      </div>

      {data.business_implications?.length > 0 && (
        <div className="bg-kip-cornflowerfaint border border-kip-cornflower/25 rounded-xl p-4 mb-3">
          <h3 className="text-xs font-body font-bold uppercase tracking-wide text-kip-cornflowerdark mb-3">What This Means for Your Business</h3>
          <ul className="space-y-2">
            {data.business_implications.map((impl, i) => (
              <li key={i} className="flex items-start gap-2 text-sm font-body text-kip-charcoal/80">
                <span className="text-kip-cornflower mt-1 shrink-0">›</span>{impl}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex items-start gap-3 text-xs font-body text-kip-muted">
        {data.forecast_note && <p className="flex-1 italic">📌 Watch: {data.forecast_note}</p>}
        {data.sources?.length > 0 && (
          <div className="flex items-center gap-1.5 shrink-0"><BookOpen size={11} /><span>{data.sources.join(' · ')}</span></div>
        )}
      </div>
    </motion.div>
  )
}
