import { motion } from 'framer-motion'
import { Clock, MapPin, Lightbulb } from 'lucide-react'
import { RegulatoryData } from '@/types'

interface Props { data: RegulatoryData }
export default function RegulatoryLayout({ data }: Props) {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-2xl">
      <div className="rounded-2xl bg-kip-navymid/8 border border-kip-navymid/20 p-5 mb-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-kip-cornflower/15 border border-kip-cornflower/30 mb-3">
          <span className="text-kip-cornflowerdark text-xs font-mono font-semibold tracking-widest uppercase">Registration Checklist</span>
        </div>
        <h2 className="font-display font-bold text-2xl text-kip-charcoal mb-1">{data.business_type}</h2>
        <div className="flex items-center gap-4 text-sm font-body text-kip-muted">
          <span className="flex items-center gap-1.5"><Clock size={13} /> {data.total_time}</span>
          <span className="font-mono font-semibold text-kip-cornflowerdark">K{data.total_cost_min.toLocaleString()}–K{data.total_cost_max.toLocaleString()} total</span>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        {data.checklist.map((item, i) => (
          <motion.div key={i} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 + i * 0.08 }}
            className="bg-white border border-kip-light rounded-xl p-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-full bg-kip-cornflower/15 mt-0.5">
                <span className="font-mono text-xs font-bold text-kip-cornflower">{item.step}</span>
              </div>
              <div className="flex-1">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="font-body font-semibold text-sm text-kip-charcoal">{item.institution}</span>
                    <span className="text-kip-muted text-sm font-body"> — {item.action}</span>
                  </div>
                  {item.status === 'mandatory' && (
                    <span className="text-xs font-mono text-red-500 bg-red-50 px-2 py-0.5 rounded-full shrink-0 border border-red-100">Required</span>
                  )}
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
                  <span className="text-xs font-mono text-kip-cornflower font-semibold">
                    {item.cost_zmw > 0 ? `K${item.cost_zmw.toLocaleString()}` : 'Free'}
                  </span>
                  <span className="flex items-center gap-1 text-xs text-kip-muted"><Clock size={10} /> {item.timeframe}</span>
                  {item.where && <span className="flex items-center gap-1 text-xs text-kip-muted"><MapPin size={10} /> {item.where}</span>}
                </div>
                {item.documents?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {item.documents.map((doc, j) => (
                      <span key={j} className="text-xs bg-kip-light border border-kip-light px-2 py-0.5 rounded text-kip-muted">{doc}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="flex items-start gap-3 bg-kip-cornflowerfaint border border-kip-cornflower/25 rounded-xl p-4">
        <Lightbulb size={16} className="text-kip-cornflower mt-0.5 shrink-0" />
        <p className="text-sm font-body text-kip-charcoal/80">
          <span className="font-semibold text-kip-cornflowerdark">Pro tip: </span>{data.pro_tip}
        </p>
      </div>
    </motion.div>
  )
}
