import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TrendingUp, TrendingDown, ExternalLink, RefreshCw, Wifi, WifiOff, BarChart3, Globe } from 'lucide-react'
import { fetchNewsAndIndicators } from '@/hooks/useAPI'

const CATEGORY_COLORS: Record<string, string> = {
  Economy:     'bg-kip-cornflower/15 text-kip-cornflower border-kip-cornflower/30',
  Prices:      'bg-amber-500/15 text-amber-400 border-amber-500/30',
  Development: 'bg-green-500/15 text-green-400 border-green-500/30',
  Mining:      'bg-orange-500/15 text-orange-400 border-orange-500/30',
  Finance:     'bg-purple-500/15 text-purple-400 border-purple-500/30',
  Agriculture: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  Business:    'bg-blue-500/15 text-blue-400 border-blue-500/30',
  General:     'bg-kip-navylight/60 text-white/40 border-kip-navylight',
}

export default function NewsPanel() {
  const [data, setData]       = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(false)
  const [tab, setTab]         = useState<'news' | 'indicators'>('news')

  const load = async () => {
    setLoading(true); setError(false)
    try {
      const result = await fetchNewsAndIndicators()
      setData(result)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const news       = data?.news       || []
  const indicators = data?.indicators || []
  const isLive     = data?.live       || false
  const updated    = data?.last_updated
    ? new Date(data.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : null

  return (
    <div className="h-full overflow-y-auto bg-kip-navy">
      {/* Header */}
      <div className="sticky top-0 z-10 border-b border-kip-navylight px-6 py-4"
        style={{ background: 'rgba(10,22,40,0.95)', backdropFilter: 'blur(8px)' }}>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="font-display font-bold text-xl text-white">Zambia Intelligence</h1>
            <div className="flex items-center gap-2 mt-0.5">
              {isLive
                ? <><Wifi size={11} className="text-green-400"/><span className="text-xs font-mono text-green-400">LIVE</span></>
                : <><WifiOff size={11} className="text-white/30"/><span className="text-xs font-mono text-white/30">CACHED</span></>
              }
              {updated && <span className="text-xs text-white/25 font-mono">· Updated {updated}</span>}
            </div>
          </div>
          <button onClick={load}
            className="flex items-center gap-1.5 text-xs text-white/40 hover:text-kip-cornflower transition-colors font-body">
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-kip-navymid rounded-xl p-1">
          {([['news', Globe, 'News Feed'], ['indicators', BarChart3, 'Economic Data']] as const).map(([id, Icon, label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-body font-semibold transition-all ${
                tab === id ? 'bg-kip-cornflower text-white' : 'text-white/40 hover:text-white/70'
              }`}>
              <Icon size={13}/>{label}
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 py-4">
        {loading && !data && (
          <div className="flex flex-col items-center justify-center py-16">
            <RefreshCw size={20} className="text-kip-cornflower animate-spin mb-3" />
            <p className="text-sm font-body text-white/40">Fetching live Zambian data...</p>
          </div>
        )}

        {error && !data && (
          <div className="text-center py-12">
            <p className="text-sm text-red-400 font-body mb-3">Could not fetch live data</p>
            <button onClick={load} className="text-xs text-kip-cornflower hover:underline font-body">Try again</button>
          </div>
        )}

        <AnimatePresence mode="wait">
          {/* NEWS TAB */}
          {tab === 'news' && (
            <motion.div key="news" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {news.length === 0 && !loading && (
                <p className="text-center text-sm text-white/30 font-body py-12">No articles available</p>
              )}
              <div className="space-y-3">
                {news.map((article: any, i: number) => (
                  <motion.a key={i} href={article.url} target="_blank" rel="noopener noreferrer"
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
                    className="group block rounded-xl border p-4 transition-all cursor-pointer"
                    style={{ background: 'rgba(13,31,60,0.8)', borderColor: 'rgba(100,149,237,0.1)' }}
                    onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(100,149,237,0.35)')}
                    onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(100,149,237,0.1)')}>

                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full border font-mono font-semibold ${CATEGORY_COLORS[article.category] || CATEGORY_COLORS.General}`}>
                        {article.category}
                      </span>
                      {article.fetched && (
                        <span className="text-xs font-mono text-green-400/70 flex items-center gap-1">
                          <Wifi size={9}/> Live
                        </span>
                      )}
                      <span className="text-xs text-white/25 font-mono ml-auto">{article.date}</span>
                    </div>

                    <h3 className="font-display font-semibold text-white text-sm leading-snug mb-1.5
                                   group-hover:text-kip-cornflower transition-colors">
                      {article.headline}
                    </h3>
                    <p className="text-xs font-body text-white/40 leading-relaxed line-clamp-2">
                      {article.summary}
                    </p>
                    <div className="flex items-center gap-1 mt-2 text-xs text-white/20 group-hover:text-kip-cornflower/50 transition-colors">
                      <ExternalLink size={10}/><span className="font-mono">{article.source}</span>
                    </div>
                  </motion.a>
                ))}
              </div>
            </motion.div>
          )}

          {/* INDICATORS TAB */}
          {tab === 'indicators' && (
            <motion.div key="indicators" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <p className="text-xs text-white/30 font-mono mb-4">
                Sources: World Bank API · ZamStats · Bank of Zambia · LME · FRA
              </p>
              <div className="grid grid-cols-2 gap-2">
                {indicators.map((ind: any, i: number) => (
                  <motion.div key={i} initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.04 }}
                    className="rounded-xl p-3 border"
                    style={{ background: 'rgba(22,43,77,0.7)', borderColor: 'rgba(100,149,237,0.12)' }}>
                    <div className="flex items-center justify-between mb-1.5">
                      <p className="text-xs font-body text-white/40 leading-snug">{ind.label}</p>
                      {ind.trend === 'up'
                        ? <TrendingUp size={12} className="text-green-400 flex-shrink-0"/>
                        : <TrendingDown size={12} className="text-red-400 flex-shrink-0"/>
                      }
                    </div>
                    <p className="font-mono font-bold text-lg text-white leading-none">{ind.value}</p>
                    <p className="text-[10px] font-mono text-kip-cornflower/50 mt-1 truncate">{ind.source}</p>
                    <p className="text-[10px] font-body text-white/20 mt-0.5 truncate">{ind.note}</p>
                  </motion.div>
                ))}
              </div>

              <div className="mt-4 p-3 rounded-xl border border-kip-cornflower/15 bg-kip-cornflower/5">
                <p className="text-xs font-body text-white/40 leading-relaxed">
                  <span className="text-kip-cornflower font-semibold">World Bank API: </span>
                  Economic indicators auto-refresh every 24 hours directly from the World Bank Open Data API.
                  Live indicators shown with source date. Fallback values used when API is unavailable.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
