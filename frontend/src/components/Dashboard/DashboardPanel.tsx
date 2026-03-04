import ExchangeRatePanel from '@/components/ui/ExchangeRatePanel'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, DollarSign, Pickaxe, RefreshCw } from 'lucide-react'
import { useKIPStore } from '@/store/kipStore'
import { getAllForecasts } from '@/hooks/useAPI'
import ForecastChart from './ForecastChart'
import { CPIIndicator } from '@/types'


export default function DashboardPanel() {
  const { metrics, gdpForecast, inflationForecast, cpiIndicators, setDashboardData } = useKIPStore()
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)

  const load = async () => {
    setLoading(true); setError(null)
    try {
      const data = await getAllForecasts()
      setDashboardData({ metrics: data.metrics, gdp: data.gdp, inflation: data.inflation, cpi: data.cpi })
    } catch {
      setError('Could not load forecast data. Is the KIP backend running?')
    } finally { setLoading(false) }
  }
  useEffect(() => { if (!metrics) load() }, [])

  if (loading && !metrics) return (
    <div className="flex items-center justify-center h-full bg-kip-offwhite">
      <div className="text-center">
        <RefreshCw className="animate-spin text-kip-cornflower mx-auto mb-3" size={24} />
        <p className="font-body text-sm text-kip-muted">Loading economic intelligence...</p>
      </div>
    </div>
  )

  if (error) return (
    <div className="flex items-center justify-center h-full bg-kip-offwhite p-8">
      <div className="text-center bg-white border border-red-100 rounded-2xl p-8 max-w-md">
        <p className="font-body text-sm text-red-600 mb-4">{error}</p>
        <button onClick={load} className="text-sm font-body text-kip-cornflower hover:underline">Retry</button>
      </div>
    </div>
  )

  return (
    <div className="h-full overflow-y-auto bg-kip-offwhite px-6 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display font-bold text-2xl text-kip-charcoal">Economic Intelligence</h1>
          <p className="font-body text-xs text-kip-muted mt-0.5">LSTM forecasts from World Bank & ZamStats data</p>
        </div>
        <button onClick={load} className="flex items-center gap-1.5 text-xs font-body text-kip-muted hover:text-kip-cornflower transition-colors">
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Top Metrics */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Food Inflation',     value: `${metrics.food_inflation}%`,            icon: <TrendingUp size={14} />, note: 'Annual' },
            { label: 'Non-Food Inflation', value: `${metrics.nonfood_inflation}%`,          icon: <TrendingUp size={14} />, note: 'Annual' },
            { label: 'USD / ZMW',          value: `K${metrics.usd_zmw.toFixed(2)}`,         icon: <DollarSign size={14} />, note: 'Approx.' },
            { label: 'Copper Price',       value: `$${(metrics.copper_usd_ton/1000).toFixed(1)}k/t`, icon: <Pickaxe size={14} />, note: 'LME' },
          ].map((m, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
              className="bg-white border border-kip-light rounded-xl p-4 shadow-card">
              <div className="flex items-center gap-2 text-kip-muted mb-2">{m.icon}<span className="text-xs font-body">{m.label}</span></div>
              <div className="font-mono text-xl font-bold text-kip-charcoal">{m.value}</div>
              <p className="text-xs text-kip-muted font-body mt-0.5">{m.note}</p>
            </motion.div>
          ))}
        </div>
      )}

      {/* LSTM Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        {gdpForecast      && <ForecastChart data={gdpForecast}      color="#0A1628" title="GDP Growth Rate"       unit="%" />}
        {inflationForecast && <ForecastChart data={inflationForecast} color="#DC2626" title="Annual Inflation Rate" unit="%" />}
      </div>

      {/* CPI Cards */}
      {cpiIndicators.length > 0 && (
        <>
          <div className="flex items-center gap-3 mb-3">
            <h2 className="font-display font-bold text-xl text-kip-charcoal">Commodity Price Intelligence</h2>
          </div>
          <p className="text-xs font-body text-kip-muted mb-4">Source: ZamStats CPI · Base year 2016 = 100</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {cpiIndicators.map((ind, i) => <CPICard key={i} indicator={ind} index={i} />)}
          </div>
        </>
      )}
    </div>
  )
}

function CPICard({ indicator, index }: { indicator: CPIIndicator; index: number }) {
  const isUp = indicator.trend === 'up'
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + index * 0.05 }}
      className="bg-white border border-kip-light rounded-xl p-4 shadow-card hover:shadow-card-hover transition-shadow">
      <div className="h-0.5 w-12 rounded-full mb-3" style={{ backgroundColor: indicator.color }} />
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-body font-semibold text-sm text-kip-charcoal pr-2 leading-snug">{indicator.name}</h3>
        <span className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded-md flex-shrink-0 ${isUp ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-700'}`}>
          {isUp ? '+' : ''}{indicator.yoy_pct?.toFixed(1)}%
        </span>
      </div>
     {/* notification*/}
      <div className="bg-kip-navymid rounded-2xl p-5 border border-white/8">
          <ExchangeRatePanel />
      </div>
      <div className="font-mono text-xl font-bold text-kip-charcoal mb-1">{indicator.current?.toFixed(1)}</div>
      <p className="text-xs text-kip-muted font-body mb-2">Current index (2016 base)</p>
      <div className="flex items-center justify-between text-xs font-body">
        <span className="text-kip-muted">12m forecast:</span>
        <span className="font-mono font-semibold" style={{ color: indicator.color }}>{indicator.forecast_12m?.toFixed(1)}</span>
      </div>
      <p className="text-xs text-kip-muted font-body mt-2 italic border-t border-kip-light pt-2">{indicator.seasonal_tip}</p>
    </motion.div>
  )
}
