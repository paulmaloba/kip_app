import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Plus, TrendingUp, AlertTriangle, Star, Package, Users, Truck, FileText, Cpu } from 'lucide-react'
import { useKIPStore } from '@/store/kipStore'
import { addBusinessLog, getBusinessLogs } from '@/hooks/useAPI'
import { BusinessLog, LogType } from '@/types'

const LOG_TYPES: { value: LogType; label: string; icon: any; color: string }[] = [
  { value: 'revenue',   label: 'Revenue',   icon: TrendingUp,   color: 'text-green-600 bg-green-50' },
  { value: 'expense',   label: 'Expense',   icon: FileText,     color: 'text-red-600 bg-red-50' },
  { value: 'challenge', label: 'Challenge', icon: AlertTriangle,color: 'text-amber-600 bg-amber-50' },
  { value: 'milestone', label: 'Milestone', icon: Star,         color: 'text-kip-cornflower bg-kip-cornflowerfaint' },
  { value: 'customer',  label: 'Customer',  icon: Users,        color: 'text-blue-600 bg-blue-50' },
  { value: 'supplier',  label: 'Supplier',  icon: Truck,        color: 'text-kip-cornflowerdark bg-kip-cornflowerfaint' },
  { value: 'general',   label: 'General',   icon: FileText,     color: 'text-kip-muted bg-kip-light' },
]

export default function JourneyPanel() {
  const { activeBusiness, userId } = useKIPStore()
  const [logs, setLogs]       = useState<BusinessLog[]>([])
  const [showForm, setShowForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm]       = useState({ log_type: 'general', title: '', description: '', amount_zmw: '' })
  const [kipFeedback, setKipFeedback] = useState<any>(null)

  useEffect(() => {
    if (activeBusiness?.id) getBusinessLogs(activeBusiness.id).then(r => setLogs(r.logs || []))
  }, [activeBusiness?.id])

  const handleSubmit = async () => {
    if (!activeBusiness || !form.title.trim() || !userId) return
    setSubmitting(true)
    try {
      const result = await addBusinessLog(activeBusiness.id, {
        user_id: userId, log_type: form.log_type, title: form.title,
        description: form.description, amount_zmw: form.amount_zmw ? parseFloat(form.amount_zmw) : undefined,
      })
      setKipFeedback(result.analysis)
      setLogs(prev => [{ id: result.log_id, ...form, amount_zmw: form.amount_zmw ? parseFloat(form.amount_zmw) : null, kip_analysis: result.analysis?.analysis, kip_suggestions: result.analysis?.suggestions || [], created_at: new Date().toISOString() } as any, ...prev])
      setForm({ log_type: 'general', title: '', description: '', amount_zmw: '' })
      setShowForm(false)
    } finally { setSubmitting(false) }
  }

  if (!activeBusiness) return (
    <div className="flex items-center justify-center h-full bg-kip-offwhite p-8">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 rounded-2xl bg-kip-light border border-kip-cornflower/20 flex items-center justify-center mx-auto mb-4">
          <Package size={24} className="text-kip-cornflower" />
        </div>
        <h2 className="font-display font-bold text-xl text-kip-charcoal mb-2">No Active Business Journey</h2>
        <p className="font-body text-sm text-kip-muted">Ask KIP for a business idea, then click "Start this Business Journey" to begin tracking your progress.</p>
      </div>
    </div>
  )

  return (
    <div className="h-full overflow-y-auto bg-kip-offwhite px-6 py-6">
      {/* Header */}
      <div className="rounded-2xl p-5 mb-6 relative overflow-hidden shadow-navy" style={{ background: 'linear-gradient(135deg, #0A1628 0%, #0D1F3C 100%)' }}>
        <div className="absolute inset-0 neural-overlay pointer-events-none" />
        <div className="relative">
          <p className="font-body text-xs text-kip-cornflower/70 uppercase tracking-widest mb-1">Active Journey</p>
          <h1 className="font-display font-bold text-2xl text-white mb-1">{activeBusiness.name}</h1>
          <div className="flex items-center gap-3 text-sm font-body text-white/50">
            <span>{activeBusiness.sector}</span><span>·</span>
            <span>{activeBusiness.location}</span><span>·</span>
            <span className="capitalize text-kip-cornflower">{activeBusiness.stage}</span>
          </div>
        </div>
      </div>

      {/* KIP Feedback */}
      {kipFeedback && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          className="bg-kip-cornflowerfaint border border-kip-cornflower/30 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Cpu size={14} className="text-kip-cornflower" />
            <p className="font-body text-xs text-kip-cornflowerdark uppercase tracking-wide font-bold">KIP Analysis</p>
          </div>
          <p className="text-sm font-body text-kip-charcoal mb-3">{kipFeedback.analysis}</p>
          {kipFeedback.suggestions?.length > 0 && (
            <div className="space-y-1.5">
              {kipFeedback.suggestions.map((s: any, i: number) => (
                <div key={i} className="flex items-start gap-2 text-xs font-body">
                  <span className={`px-1.5 py-0.5 rounded text-white text-[10px] font-semibold flex-shrink-0 ${s.priority === 'high' ? 'bg-red-500' : s.priority === 'medium' ? 'bg-amber-500' : 'bg-kip-muted'}`}>{s.priority}</span>
                  <span className="text-kip-charcoal">{s.action}</span>
                  <span className="text-kip-muted ml-auto shrink-0">{s.timeframe}</span>
                </div>
              ))}
            </div>
          )}
          {kipFeedback.encouragement && (
            <p className="text-xs italic text-kip-muted mt-3 border-t border-kip-cornflower/15 pt-3">✨ {kipFeedback.encouragement}</p>
          )}
        </motion.div>
      )}

      {/* Add Log */}
      <button onClick={() => setShowForm(true)}
        className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border-2 border-dashed border-kip-cornflower/30
                   text-kip-cornflower hover:bg-kip-cornflowerfaint hover:border-kip-cornflower/50 transition-all font-body font-semibold text-sm mb-5">
        <Plus size={16} /> Add Business Update
      </button>

      {/* Log Form */}
      {showForm && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className="bg-white border border-kip-light rounded-xl p-5 mb-4 shadow-card">
          <h3 className="font-body font-semibold text-sm text-kip-charcoal mb-4">New Business Log</h3>
          <div className="flex flex-wrap gap-2 mb-4">
            {LOG_TYPES.map(lt => (
              <button key={lt.value} onClick={() => setForm(f => ({ ...f, log_type: lt.value }))}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-body font-semibold transition-all border ${
                  form.log_type === lt.value ? 'border-kip-cornflower/40 bg-kip-cornflowerfaint text-kip-cornflowerdark' : 'border-kip-light text-kip-muted hover:border-kip-light'
                }`}>
                <lt.icon size={11} />{lt.label}
              </button>
            ))}
          </div>
          <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            placeholder="What happened?" className="w-full border border-kip-light rounded-lg px-3 py-2 text-sm font-body mb-3 focus:outline-none focus:ring-2 focus:ring-kip-cornflower/20" />
          <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            placeholder="More details (optional)" rows={2}
            className="w-full border border-kip-light rounded-lg px-3 py-2 text-sm font-body mb-3 focus:outline-none focus:ring-2 focus:ring-kip-cornflower/20 resize-none" />
          <input value={form.amount_zmw} onChange={e => setForm(f => ({ ...f, amount_zmw: e.target.value }))}
            type="number" placeholder="Amount in ZMW (optional)"
            className="w-full border border-kip-light rounded-lg px-3 py-2 text-sm font-mono mb-4 focus:outline-none focus:ring-2 focus:ring-kip-cornflower/20" />
          <div className="flex gap-2">
            <button onClick={handleSubmit} disabled={!form.title.trim() || submitting}
              className="flex-1 py-2.5 rounded-lg bg-kip-cornflower text-white font-body font-semibold text-sm disabled:opacity-50 hover:bg-kip-cornflowerdark transition-colors">
              {submitting ? 'Sending to KIP...' : 'Submit & Get KIP Analysis'}
            </button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2.5 rounded-lg border border-kip-light text-kip-muted text-sm font-body">Cancel</button>
          </div>
        </motion.div>
      )}

      {/* Logs */}
      <div className="space-y-3">
        {logs.map((log, i) => {
          const typeInfo = LOG_TYPES.find(lt => lt.value === log.log_type) || LOG_TYPES[LOG_TYPES.length - 1]
          return (
            <motion.div key={log.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
              className="bg-white border border-kip-light rounded-xl p-4 shadow-card">
              <div className="flex items-start gap-3">
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${typeInfo.color}`}>
                  <typeInfo.icon size={13} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-body font-semibold text-sm text-kip-charcoal truncate">{log.title}</p>
                    {log.amount_zmw && <span className="font-mono text-xs font-bold text-kip-cornflower flex-shrink-0">K{log.amount_zmw.toLocaleString()}</span>}
                  </div>
                  {log.description && <p className="text-xs font-body text-kip-muted mt-0.5 line-clamp-2">{log.description}</p>}
                  {log.kip_analysis && <p className="text-xs font-body text-kip-cornflowerdark/80 mt-2 italic">KIP: {log.kip_analysis}</p>}
                  <p className="text-xs text-kip-muted font-mono mt-1">{new Date(log.created_at).toLocaleDateString('en-ZM', { day: 'numeric', month: 'short' })}</p>
                </div>
              </div>
            </motion.div>
          )
        })}
        {logs.length === 0 && <div className="text-center py-8 text-kip-muted font-body text-sm">No logs yet. Submit your first business update above.</div>}
      </div>
    </div>
  )
}
