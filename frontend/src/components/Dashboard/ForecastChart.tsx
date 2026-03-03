import { useState, useEffect } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { ForecastData } from '@/types'

interface Props { data: ForecastData; color?: string; title?: string; unit?: string }

const CustomTooltip = ({ active, payload, label, unit }: any) => {
  if (!active || !payload?.length) return null
  const val = payload[0]?.value ?? payload[1]?.value
  const isForecast = payload.find((p: any) => p.dataKey === 'forecast')?.value !== null
  return (
    <div className="bg-kip-navy text-white text-xs rounded-lg px-3 py-2 shadow-navy font-body border border-kip-cornflower/30">
      <p className="text-white/50 mb-0.5">{label}</p>
      <p className="font-mono font-bold">{val?.toFixed(2)}{unit}</p>
      {isForecast && <p className="text-kip-cornflower text-xs mt-0.5">↑ LSTM Forecast</p>}
    </div>
  )
}

export default function ForecastChart({ data, color = '#0D1F3C', title, unit = '%' }: Props) {
  const [animatedData, setAnimatedData] = useState<any[]>([])
  const [showForecast, setShowForecast] = useState(false)

  useEffect(() => {
    if (!data?.chart_data) return
    setAnimatedData([]); setShowForecast(false)
    const hist = data.chart_data.filter(d => d.historical !== null)
    const fc   = data.chart_data.filter(d => d.forecast !== null)
    let i = 0
    const histTimer = setInterval(() => {
      if (i >= hist.length) {
        clearInterval(histTimer)
        setTimeout(() => {
          setShowForecast(true)
          let j = 0
          const fcTimer = setInterval(() => {
            if (j >= fc.length) { clearInterval(fcTimer); return }
            setAnimatedData(prev => [...prev, fc[j]]); j++
          }, 60)
        }, 300)
        return
      }
      setAnimatedData(prev => [...prev, hist[i]]); i++
    }, 40)
    return () => clearInterval(histTimer)
  }, [data])

  const chartData = data?.chart_data ?? []
  const current = data?.current ?? 0
  const fc12    = data?.forecast_12m ?? 0
  const change  = fc12 - current
  const boundaryIdx = chartData.findIndex(d => d.historical === null)

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl border border-kip-light p-5 shadow-card">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-display font-bold text-lg text-kip-charcoal">{title || data?.indicator}</h3>
          <p className="text-xs text-kip-muted font-body mt-0.5">{data?.model_source}</p>
        </div>
        <div className="text-right">
          <div className="font-mono text-2xl font-bold text-kip-charcoal">{current.toFixed(1)}{unit}</div>
          <div className={`flex items-center justify-end gap-1 text-xs font-mono mt-1 ${change >= 0 ? 'text-status-up' : 'text-status-down'}`}>
            {change >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            12m: {change >= 0 ? '+' : ''}{change.toFixed(1)}{unit}
          </div>
        </div>
      </div>

      {/* Forecast badges */}
      <div className="flex gap-2 mb-4">
        {[{ label:'+3m', value:data?.forecast_3m }, { label:'+6m', value:data?.forecast_6m }, { label:'+12m', value:data?.forecast_12m }].map((fc, i) => (
          <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: showForecast ? 1 : 0 }} transition={{ delay: i * 0.15 }}
            className="flex-1 text-center bg-kip-cornflowerfaint border border-kip-cornflower/25 rounded-lg py-1.5 px-2">
            <p className="text-xs text-kip-muted font-body">{fc.label}</p>
            <p className="font-mono text-sm font-bold text-kip-cornflower">{fc.value?.toFixed(1)}{unit}</p>
          </motion.div>
        ))}
      </div>

      {/* Chart */}
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
            <defs>
              <linearGradient id={`grad-hist`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={color}      stopOpacity={0.15} />
                <stop offset="95%" stopColor={color}      stopOpacity={0} />
              </linearGradient>
              <linearGradient id="grad-fc" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#6495ED" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#6495ED" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E8EFF8" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#6B7A99' }} tickLine={false} axisLine={false} interval={5} />
            <YAxis tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#6B7A99' }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}${unit}`} />
            <Tooltip content={<CustomTooltip unit={unit} />} />
            {boundaryIdx > 0 && <ReferenceLine x={chartData[boundaryIdx]?.date} stroke="#6495ED" strokeDasharray="4 4" strokeOpacity={0.5} />}
            <Area type="monotone" dataKey="historical" stroke={color} strokeWidth={2} fill="url(#grad-hist)" connectNulls={false} dot={false} animationDuration={800} />
            <Area type="monotone" dataKey="forecast" stroke="#6495ED" strokeWidth={2} strokeDasharray="6 3" fill="url(#grad-fc)" connectNulls={false} dot={false} animationDuration={1200} animationBegin={showForecast ? 0 : 99999} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-4 mt-3 justify-center">
        <div className="flex items-center gap-1.5"><div className="w-6 h-0.5" style={{ backgroundColor: color }} /><span className="text-xs text-kip-muted font-body">Historical</span></div>
        <div className="flex items-center gap-1.5"><div className="w-6 h-0.5 border-t-2 border-dashed border-kip-cornflower" /><span className="text-xs text-kip-muted font-body">LSTM Forecast</span></div>
      </div>
    </motion.div>
  )
}
