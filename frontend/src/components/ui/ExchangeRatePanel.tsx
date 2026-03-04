import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Minus, RefreshCw, AlertTriangle } from 'lucide-react'
import axios from 'axios'

const BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api'

interface RatePair {
  currency:     string
  label:        string
  rate_vs_usd:  number
  zmw_per_unit: number | null
  display:      string
}

interface Alert {
  currency:   string
  label:      string
  pct_change: number
  message:    string
  impact:     string
  severity:   string
  timestamp:  string
}

const CURRENCY_FLAGS: Record<string, string> = {
  ZMW: '🇿🇲', USD: '🇺🇸', GBP: '🇬🇧', EUR: '🇪🇺',
  ZAR: '🇿🇦', CNY: '🇨🇳', BWP: '🇧🇼', TZS: '🇹🇿', MWK: '🇲🇼',
}

export default function ExchangeRatePanel() {
  const [pairs,      setPairs]      = useState<RatePair[]>([])
  const [alerts,     setAlerts]     = useState<Alert[]>([])
  const [zmwPerUsd,  setZmwPerUsd]  = useState<number | null>(null)
  const [source,     setSource]     = useState<string>('loading')
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const [loading,    setLoading]    = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchRates = async (manual = false) => {
    if (manual) setRefreshing(true)
    try {
      const { data } = await axios.get(`${BASE}/rates/current`)
      const summary = data.summary
      setPairs(summary.pairs || [])
      setZmwPerUsd(summary.zmw_per_usd)
      setSource(data.source)
      setLastUpdate(new Date(summary.timestamp).toLocaleTimeString())
      setAlerts(data.recent_alerts || [])
    } catch (e) {
      console.error('Failed to fetch rates', e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchRates()
    const interval = setInterval(() => fetchRates(), 3600000) // refresh every hour
    return () => clearInterval(interval)
  }, [])

  // ZMW row — always first
  const zmwPair = pairs.find(p => p.currency === 'ZMW')
  const otherPairs = pairs.filter(p => p.currency !== 'ZMW')

  if (loading) {
    return (
      <div className="animate-pulse space-y-3 p-4">
        <div className="h-20 bg-white/5 rounded-xl" />
        <div className="h-12 bg-white/5 rounded-xl" />
        <div className="h-12 bg-white/5 rounded-xl" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-display font-bold text-white text-base">Live Exchange Rates</h3>
          <p className="font-body text-white/30 text-xs">
            {source === 'live' ? '🟢 Live data' : source === 'cache' ? '🟡 Cached' : '🔴 Estimated'}
            {lastUpdate && ` · Updated ${lastUpdate}`}
          </p>
        </div>
        <button onClick={() => fetchRates(true)}
          disabled={refreshing}
          className="p-2 rounded-xl text-white/30 hover:text-white hover:bg-white/8 transition-colors">
          <RefreshCw size={15} className={refreshing ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Hero — USD/ZMW */}
      {zmwPair && (
        <div className="p-4 rounded-2xl border border-kip-cornflower/30"
             style={{ background: 'linear-gradient(135deg, rgba(100,149,237,0.15), rgba(100,149,237,0.05))' }}>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-body text-white/50 text-xs mb-1">🇺🇸 USD → 🇿🇲 ZMW</p>
              <p className="font-display font-bold text-white text-3xl">
                K{zmwPair.rate_vs_usd.toFixed(2)}
              </p>
              <p className="font-body text-white/40 text-xs mt-1">1 US Dollar</p>
            </div>
            <div className="text-right">
              <p className="font-body text-white/50 text-xs mb-1">ZMW → USD</p>
              <p className="font-display font-bold text-kip-cornflower text-xl">
                ${(1 / zmwPair.rate_vs_usd).toFixed(4)}
              </p>
              <p className="font-body text-white/40 text-xs mt-1">1 Kwacha</p>
            </div>
          </div>
        </div>
      )}

      {/* Other pairs grid */}
      <div className="grid grid-cols-2 gap-2">
        {otherPairs.map((pair) => (
          <div key={pair.currency}
            className="p-3 rounded-xl bg-white/5 border border-white/8 hover:border-white/15 transition-colors">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-base">{CURRENCY_FLAGS[pair.currency] || '💱'}</span>
              <span className="font-body text-white/40 text-xs">{pair.currency}</span>
            </div>
            <p className="font-display font-bold text-white text-base">
              {pair.zmw_per_unit
                ? `K${pair.zmw_per_unit.toFixed(2)}`
                : pair.display}
            </p>
            <p className="font-body text-white/25 text-[10px] mt-0.5 truncate">
              1 {pair.currency} = {pair.zmw_per_unit ? `K${pair.zmw_per_unit.toFixed(2)}` : '—'}
            </p>
          </div>
        ))}
      </div>

      {/* Active alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          <p className="font-body font-bold text-white/50 text-xs uppercase tracking-widest">
            Recent Movements
          </p>
          {alerts.slice(0, 3).map((alert, i) => {
            const isDown = alert.pct_change > 0 && alert.currency === 'ZMW'
            const isMajor = alert.severity === 'major'
            return (
              <div key={i}
                className={`p-3 rounded-xl border text-xs ${
                  isMajor
                    ? 'bg-red-500/10 border-red-500/30'
                    : isDown
                    ? 'bg-amber-500/10 border-amber-500/30'
                    : 'bg-green-500/10 border-green-500/30'
                }`}>
                <div className="flex items-start gap-2">
                  {isMajor ? (
                    <AlertTriangle size={12} className="text-red-400 flex-shrink-0 mt-0.5" />
                  ) : isDown ? (
                    <TrendingDown size={12} className="text-amber-400 flex-shrink-0 mt-0.5" />
                  ) : (
                    <TrendingUp size={12} className="text-green-400 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <p className="font-body font-semibold text-white/80">{alert.message}</p>
                    <p className="font-body text-white/40 mt-0.5">{alert.impact}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Business tips */}
      {zmwPerUsd && (
        <div className="p-3 rounded-xl bg-kip-navy border border-white/8">
          <p className="font-body font-bold text-white/50 text-[10px] uppercase tracking-widest mb-2">
            KIP Business Insight
          </p>
          <p className="font-body text-white/60 text-xs leading-relaxed">
            {zmwPerUsd > 28
              ? '⚠️ Kwacha under pressure. If you import goods, consider buying USD now or negotiating ZMW contracts. Local produce becomes more competitive vs imports.'
              : zmwPerUsd < 25
              ? '✅ Kwacha is relatively strong. Good time to import equipment or pay USD loans. Export revenues in ZMW are lower — plan accordingly.'
              : '📊 Kwacha is trading in a stable range. Normal business planning applies.'}
          </p>
        </div>
      )}

      <p className="font-body text-white/15 text-[10px] text-center">
        Rates indicative only · Always verify with your bank · Updates hourly
      </p>
    </div>
  )
}
