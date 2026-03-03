import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TrendingUp, TrendingDown, ArrowRight, RefreshCw, ExternalLink, BarChart3, Globe, Cpu, Wifi, WifiOff } from 'lucide-react'
import { fetchNewsAndIndicators } from '@/hooks/useAPI'

interface Props { onEnter: () => void }

const CATEGORY_COLORS: Record<string, string> = {
  Economy:     'bg-kip-cornflower/20 text-kip-cornflower border-kip-cornflower/30',
  Prices:      'bg-amber-500/15 text-amber-400 border-amber-500/30',
  Development: 'bg-green-500/15 text-green-400 border-green-500/30',
  Mining:      'bg-orange-500/15 text-orange-400 border-orange-500/30',
  Finance:     'bg-purple-500/15 text-purple-400 border-purple-500/30',
  Agriculture: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  Business:    'bg-blue-500/15 text-blue-400 border-blue-500/30',
  General:     'bg-white/5 text-white/40 border-white/10',
}

// Animated KIP Logo (inline SVG React component)
function KIPLogo({ size = 120, thinking = false }: { size?: number; thinking?: boolean }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width={size} height={size}>
      <defs>
        <radialGradient id="lbg2" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#0D1F3C"/><stop offset="100%" stopColor="#0A1628"/>
        </radialGradient>
        <linearGradient id="lnote2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1a6b3a"/><stop offset="50%" stopColor="#22883f"/><stop offset="100%" stopColor="#156030"/>
        </linearGradient>
        <linearGradient id="lmd2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#2A3F6B"/><stop offset="100%" stopColor="#162B4D"/>
        </linearGradient>
        <linearGradient id="lmm2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3A5490"/><stop offset="100%" stopColor="#2A3F6B"/>
        </linearGradient>
        <linearGradient id="lml2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#6495ED" stopOpacity="0.6"/><stop offset="100%" stopColor="#85B3F5" stopOpacity="0.3"/>
        </linearGradient>
        <filter id="lgw2">
          <feGaussianBlur stdDeviation="2.5" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <circle cx="200" cy="200" r="200" fill="url(#lbg2)"/>
      <ellipse cx="200" cy="220" rx="130" ry="100" fill="#6495ED" fillOpacity="0.1">
        {thinking && <animate attributeName="rx" values="130;155;130" dur="1.8s" repeatCount="indefinite"/>}
      </ellipse>
      <g transform="translate(200,148)">
        <g>
          {thinking
            ? <animateTransform attributeName="transform" type="rotate" values="-22;-33;-14;-28;-22" dur="1.6s" repeatCount="indefinite" additive="sum"/>
            : <animateTransform attributeName="transform" type="rotate" values="-22;-25;-22" dur="5s" repeatCount="indefinite" additive="sum"/>
          }
          <rect x="-78" y="-38" width="156" height="76" rx="6" fill="#000" opacity="0.3" transform="translate(4,5)"/>
          <rect x="-78" y="-38" width="156" height="76" rx="6" fill="url(#lnote2)"/>
          <rect x="-72" y="-32" width="144" height="64" rx="4" fill="none" stroke="white" strokeWidth="1.2" opacity="0.35"/>
          <ellipse cx="0" cy="0" rx="22" ry="16" fill="none" stroke="white" strokeWidth="1" opacity="0.5"/>
          <text x="0" y="5" fontFamily="Georgia,serif" fontSize="14" fontWeight="bold" fill="white" textAnchor="middle" opacity="0.8">K</text>
          <line x1="-65" y1="-8" x2="-30" y2="-8" stroke="white" strokeWidth="0.8" opacity="0.3"/>
          <line x1="-65" y1="2" x2="-30" y2="2" stroke="white" strokeWidth="0.8" opacity="0.3"/>
          <line x1="30" y1="-8" x2="65" y2="-8" stroke="white" strokeWidth="0.8" opacity="0.3"/>
          <line x1="30" y1="2" x2="65" y2="2" stroke="white" strokeWidth="0.8" opacity="0.3"/>
          <rect x="10" y="-38" width="6" height="76" fill="#6495ED" opacity="0.25"/>
          <text x="-68" y="-22" fontFamily="monospace" fontSize="9" fill="white" opacity="0.7">K50</text>
        </g>
      </g>
      <rect x="148" y="230" width="104" height="68" rx="12" fill="url(#lmm2)" stroke="#6495ED" strokeWidth="1" strokeOpacity="0.3"/>
      <line x1="200" y1="252" x2="200" y2="278" stroke="#6495ED" strokeWidth="0.7" strokeOpacity="0.4"/>
      <circle cx="200" cy="264" r="4" fill="#6495ED" opacity="0.6" filter="url(#lgw2)">
        {thinking && <animate attributeName="opacity" values="0.6;1;0.6" dur="1s" repeatCount="indefinite"/>}
      </circle>
      <circle cx="200" cy="264" r="2" fill="white" opacity="0.8"/>
      <rect x="152" y="290" width="96" height="38" rx="10" fill="url(#lmd2)" stroke="#6495ED" strokeWidth="1" strokeOpacity="0.4"/>
      {thinking && <>
        <circle cx="185" cy="309" r="2.5" fill="#6495ED"><animate attributeName="opacity" values="0.3;1;0.3" dur="1s" begin="0s" repeatCount="indefinite"/></circle>
        <circle cx="200" cy="309" r="2.5" fill="#6495ED"><animate attributeName="opacity" values="0.3;1;0.3" dur="1s" begin="0.33s" repeatCount="indefinite"/></circle>
        <circle cx="215" cy="309" r="2.5" fill="#6495ED"><animate attributeName="opacity" values="0.3;1;0.3" dur="1s" begin="0.66s" repeatCount="indefinite"/></circle>
      </>}
      {/* Fingers */}
      {[[-12,164], [-4,186], [4,214], [14,236]].map(([rot, tx], i) => (
        <g key={i} transform={`translate(${tx},230) rotate(${rot})`}>
          <rect x="-10" y="-75" width="20" height="52" rx="5" fill="url(#lmm2)" stroke="#6495ED" strokeWidth="0.8" strokeOpacity="0.4"/>
          <rect x="-11" y="-50" width="22" height="5" rx="2" fill="url(#lmd2)"/>
          <rect x="-10" y="-20" width="20" height="22" rx="4" fill="url(#lmm2)" stroke="#6495ED" strokeWidth="0.8" strokeOpacity="0.3"/>
        </g>
      ))}
      <g transform="translate(148,268) rotate(-30)">
        <rect x="-50" y="-10" width="24" height="20" rx="5" fill="url(#lmm2)" stroke="#6495ED" strokeWidth="0.8" strokeOpacity="0.5"/>
        <rect x="-28" y="-11" width="6" height="22" rx="3" fill="url(#lmd2)"/>
        <rect x="-23" y="-10" width="26" height="20" rx="4" fill="url(#lmm2)"/>
      </g>
      <line x1="154" y1="230" x2="246" y2="230" stroke="#6495ED" strokeWidth="1.5" strokeOpacity="0.5" filter="url(#lgw2)"/>
      <text x="200" y="372" fontFamily="'Arial Black',sans-serif" fontSize="30" fontWeight="900" fill="white" textAnchor="middle" letterSpacing="6" opacity="0.95">KIP</text>
      <text x="200" y="390" fontFamily="Arial,sans-serif" fontSize="8" fill="#6495ED" textAnchor="middle" letterSpacing="3" opacity="0.7">KWACHA INTELLIGENCE</text>
      <circle cx="200" cy="200" r="196" fill="none" stroke="#6495ED" strokeWidth="1" strokeOpacity="0.2"/>
    </svg>
  )
}

export default function LandingPage({ onEnter }: Props) {
  const [booting, setBooting]           = useState(true)
  const [data, setData]                 = useState<any>(null)
  const [visibleStats, setVisibleStats] = useState(0)
  const [currentNewsIdx, setCurrentNewsIdx] = useState(0)
  const tickerRef = useRef<ReturnType<typeof setInterval>>()

  // Boot: show animated logo for 2s while fetching data
  useEffect(() => {
    const boot = setTimeout(() => setBooting(false), 2000)
    fetchNewsAndIndicators()
      .then(setData)
      .catch(() => {/* fallback handled in service */})
    return () => clearTimeout(boot)
  }, [])

  const news       = data?.news       || []
  const indicators = data?.indicators || []
  const isLive     = data?.live       || false

  useEffect(() => {
    if (booting || !indicators.length) return
    let i = 0
    const t = setInterval(() => { i++; setVisibleStats(i); if (i >= indicators.length) clearInterval(t) }, 80)
    return () => clearInterval(t)
  }, [booting, indicators])

  useEffect(() => {
    if (!news.length) return
    tickerRef.current = setInterval(() => setCurrentNewsIdx(i => (i + 1) % news.length), 5000)
    return () => clearInterval(tickerRef.current)
  }, [news.length])

  const currentNews = news[currentNewsIdx] || null

  // ── Boot screen ─────────────────────────────────────────────────────────────
  if (booting) return (
    <div className="fixed inset-0 flex flex-col items-center justify-center"
      style={{ background: 'linear-gradient(135deg, #0A1628 0%, #0D1F3C 100%)' }}>
      <div className="neural-overlay absolute inset-0 pointer-events-none" />
      <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
        className="relative z-10 flex flex-col items-center">
        <KIPLogo size={140} thinking />
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
          className="font-body text-kip-cornflower/70 text-sm mt-4 tracking-widest uppercase">
          Loading Zambian Intelligence...
        </motion.p>
        <div className="flex gap-1.5 mt-4">
          {[0,1,2].map(i => (
            <div key={i} className="w-1.5 h-1.5 rounded-full bg-kip-cornflower animate-bounce"
              style={{ animationDelay: `${i * 200}ms` }}/>
          ))}
        </div>
      </motion.div>
    </div>
  )

  // ── Main landing ─────────────────────────────────────────────────────────────
  return (
    <div className="h-screen overflow-y-auto"
      style={{ background: 'linear-gradient(180deg, #0A1628 0%, #0D1F3C 40%, #0A1628 100%)' }}>
      <div className="neural-overlay fixed inset-0 pointer-events-none z-0 animate-neural" />

      <div className="relative z-10 flex flex-col items-center pt-10 pb-10 px-4">

        {/* Hero */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center text-center mb-8">
          <KIPLogo size={110} />
          <h1 className="font-display font-bold text-4xl text-white mt-4 mb-2 tracking-tight">
            Kwacha Intelligence Platform
          </h1>
          <p className="font-body text-kip-cornflower/80 text-base max-w-lg leading-relaxed">
            AI-powered business and economic intelligence built for Zambia.
            Real data. Real insights. Your next move, made clear.
          </p>
          {/* Live indicator */}
          <div className="flex items-center gap-2 mt-3">
            {isLive
              ? <><Wifi size={12} className="text-green-400"/><span className="text-xs font-mono text-green-400">Live data from World Bank · Zambian RSS</span></>
              : <><WifiOff size={12} className="text-white/30"/><span className="text-xs font-mono text-white/30">Cached data</span></>
            }
          </div>
        </motion.div>

        {/* News ticker */}
        {currentNews && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
            className="w-full max-w-3xl mb-8 rounded-xl overflow-hidden border border-kip-cornflower/20"
            style={{ background: 'rgba(100,149,237,0.07)' }}>
            <div className="flex items-center gap-3 px-4 py-2 border-b border-kip-cornflower/15">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse flex-shrink-0"/>
              <span className="text-xs font-mono font-bold text-kip-cornflower tracking-widest uppercase">
                Zambia Intelligence {isLive ? '· LIVE' : ''}
              </span>
            </div>
            <AnimatePresence mode="wait">
              <motion.div key={currentNewsIdx}
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.4 }} className="px-4 py-3 cursor-pointer group"
                onClick={() => window.open(currentNews.url, '_blank')}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full border font-mono font-semibold ${CATEGORY_COLORS[currentNews.category] || CATEGORY_COLORS.General}`}>
                        {currentNews.category}
                      </span>
                      <span className="text-xs text-white/30 font-mono">{currentNews.date}</span>
                      <span className="text-xs text-white/25 font-mono">· {currentNews.source}</span>
                    </div>
                    <p className="font-display font-semibold text-white text-base leading-snug group-hover:text-kip-cornflower transition-colors">
                      {currentNews.headline}
                    </p>
                    <p className="text-sm font-body text-white/50 mt-1 leading-relaxed line-clamp-2">
                      {currentNews.summary}
                    </p>
                  </div>
                  <ExternalLink size={14} className="text-white/25 group-hover:text-kip-cornflower flex-shrink-0 mt-1 transition-colors"/>
                </div>
                <div className="h-0.5 bg-white/10 rounded-full mt-3 overflow-hidden">
                  <motion.div key={currentNewsIdx} className="h-full bg-kip-cornflower/60 rounded-full"
                    initial={{ width: '0%' }} animate={{ width: '100%' }} transition={{ duration: 5, ease: 'linear' }}/>
                </div>
              </motion.div>
            </AnimatePresence>
            <div className="flex justify-center gap-1.5 pb-2">
              {news.map((_: any, i: number) => (
                <button key={i} onClick={() => setCurrentNewsIdx(i)}
                  className={`h-1.5 rounded-full transition-all ${i === currentNewsIdx ? 'bg-kip-cornflower w-4' : 'bg-white/20 w-1.5'}`}/>
              ))}
            </div>
          </motion.div>
        )}

        {/* Stats grid */}
        {indicators.length > 0 && (
          <div className="w-full max-w-3xl mb-8">
            <div className="flex items-center gap-3 mb-4">
              <BarChart3 size={16} className="text-kip-cornflower"/>
              <h2 className="font-display font-bold text-white text-lg">Zambia Economic Snapshot</h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {indicators.map((stat: any, i: number) => (
                <motion.div key={i}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={i < visibleStats ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.25 }}
                  className="rounded-xl p-3 border"
                  style={{ background: 'rgba(22,43,77,0.6)', borderColor: 'rgba(100,149,237,0.15)' }}>
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs font-body text-white/40 leading-snug pr-1">{stat.label}</p>
                    {stat.trend === 'up'
                      ? <TrendingUp size={11} className="text-green-400 flex-shrink-0"/>
                      : <TrendingDown size={11} className="text-red-400 flex-shrink-0"/>
                    }
                  </div>
                  <p className="font-mono font-bold text-xl text-white">{stat.value}</p>
                  <p className="text-[10px] font-mono text-kip-cornflower/50 mt-0.5 truncate">{stat.source}</p>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* News cards */}
        {news.length > 0 && (
          <div className="w-full max-w-3xl mb-10">
            <div className="flex items-center gap-3 mb-4">
              <Globe size={16} className="text-kip-cornflower"/>
              <h2 className="font-display font-bold text-white text-lg">Latest from Zambia</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {news.slice(0, 6).map((article: any, i: number) => (
                <motion.a key={i} href={article.url} target="_blank" rel="noopener noreferrer"
                  initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + i * 0.08 }}
                  className="group block rounded-xl p-4 border transition-all cursor-pointer"
                  style={{ background: 'rgba(13,31,60,0.7)', borderColor: 'rgba(100,149,237,0.1)' }}
                  onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(100,149,237,0.35)')}
                  onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(100,149,237,0.1)')}>
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-mono font-semibold ${CATEGORY_COLORS[article.category] || CATEGORY_COLORS.General}`}>
                      {article.category}
                    </span>
                    {article.fetched && <Wifi size={9} className="text-green-400"/>}
                    <span className="text-xs text-white/25 font-mono ml-auto">{article.date}</span>
                  </div>
                  <h3 className="font-display font-semibold text-white text-sm leading-snug mb-1.5 group-hover:text-kip-cornflower transition-colors">
                    {article.headline}
                  </h3>
                  <p className="text-xs font-body text-white/40 leading-relaxed line-clamp-2">{article.summary}</p>
                  <div className="flex items-center gap-1 mt-2 text-xs text-white/20 group-hover:text-kip-cornflower/50 transition-colors">
                    <ExternalLink size={10}/><span>{article.source}</span>
                  </div>
                </motion.a>
              ))}
            </div>
          </div>
        )}

        {/* Enter CTA */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }} className="flex flex-col items-center text-center mb-12">
          <motion.button onClick={onEnter}
            whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
            className="flex items-center gap-3 px-8 py-4 rounded-2xl font-display font-bold text-xl text-white group shadow-glow-strong"
            style={{ background: 'linear-gradient(135deg, #4A7BD4 0%, #6495ED 100%)' }}>
            <Cpu size={22}/>
            Enter KIP Platform
            <ArrowRight size={22} className="group-hover:translate-x-1 transition-transform"/>
          </motion.button>
          <p className="text-xs font-body text-white/25 mt-3">Sign in or create a free account to get started</p>
        </motion.div>
      </div>
    </div>
  )
}
