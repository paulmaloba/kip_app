import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, BarChart2, Briefcase, ChevronLeft, ChevronRight, Cpu, Globe, LogOut, User } from 'lucide-react'
import { useKIPStore } from '@/store/kipStore'
import { authLogout } from '@/hooks/useAPI'

const NAV_ITEMS = [
  { id: 'chat',      label: 'Ask KIP',     icon: MessageSquare, desc: 'Business intelligence' },
  { id: 'dashboard', label: 'Economy',     icon: BarChart2,     desc: 'Forecasts & indicators' },
  { id: 'news',      label: 'ZM News',     icon: Globe,         desc: 'Live Zambian updates' },
  { id: 'journey',   label: 'My Business', icon: Briefcase,     desc: 'Track your journey' },
] as const

export default function Sidebar() {
  const {
    sidebarOpen, toggleSidebar, activePanel, setActivePanel,
    activeBusiness, user, refreshToken, clearAuth,
  } = useKIPStore()

  const handleLogout = async () => {
    try {
      if (refreshToken) await authLogout(refreshToken)
    } finally {
      clearAuth()
    }
  }

  return (
    <motion.aside
      animate={{ width: sidebarOpen ? 224 : 64 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="flex flex-col h-full overflow-hidden relative z-10"
      style={{ background: 'linear-gradient(180deg, #0A1628 0%, #0D1F3C 100%)' }}
    >
      <div className="absolute inset-0 neural-overlay opacity-100 pointer-events-none" />

      {/* Logo */}
      <div className="relative flex items-center gap-3 px-4 py-5 border-b border-white/8">
        <div className="w-9 h-9 rounded-xl bg-kip-cornflower/20 border border-kip-cornflower/40
                        flex items-center justify-center flex-shrink-0 cornflower-glow">
          <Cpu size={18} className="text-kip-cornflower" />
        </div>
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }} transition={{ duration: 0.2 }}>
              <div className="font-display font-bold text-white text-lg leading-none tracking-tight">KIP</div>
              <div className="font-body text-kip-cornflower/60 text-[10px] tracking-widest uppercase mt-0.5">
                Kwacha Intelligence
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Nav */}
      <nav className="relative flex-1 px-2 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon   = item.icon
          const active = activePanel === item.id
          return (
            <motion.button key={item.id} onClick={() => setActivePanel(item.id)}
              whileHover={{ x: 2 }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left ${
                active ? 'bg-kip-cornflower text-white shadow-glow' : 'text-white/40 hover:text-white hover:bg-white/8'
              }`}>
              <Icon size={18} className="flex-shrink-0" />
              <AnimatePresence>
                {sidebarOpen && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    <div className="font-body font-semibold text-sm">{item.label}</div>
                    <div className={`font-body text-[10px] ${active ? 'text-white/70' : 'text-white/30'}`}>
                      {item.desc}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>
          )
        })}
      </nav>

      {/* Active business badge */}
      {activeBusiness && sidebarOpen && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="relative mx-2 mb-2 p-3 rounded-xl bg-kip-cornflower/15 border border-kip-cornflower/30">
          <p className="font-body text-[10px] text-kip-cornflower/70 uppercase tracking-widest mb-0.5">Active Journey</p>
          <p className="font-body font-semibold text-white text-xs truncate">{activeBusiness.name}</p>
          <p className="font-body text-white/40 text-[10px] capitalize">{activeBusiness.stage}</p>
        </motion.div>
      )}

      {/* User info + logout */}
      {user && (
        <div className={`relative border-t border-white/8 px-3 py-3 ${sidebarOpen ? 'flex items-center gap-2' : 'flex justify-center'}`}>
          <div className="w-7 h-7 rounded-lg bg-kip-cornflower/20 flex items-center justify-center flex-shrink-0">
            <User size={13} className="text-kip-cornflower" />
          </div>
          <AnimatePresence>
            {sidebarOpen && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 min-w-0">
                <p className="text-xs font-body font-semibold text-white truncate">{user.name}</p>
                <p className="text-[10px] font-mono text-white/30 truncate">{user.email}</p>
              </motion.div>
            )}
          </AnimatePresence>
          {sidebarOpen && (
            <button onClick={handleLogout}
              className="text-white/25 hover:text-red-400 transition-colors flex-shrink-0" title="Sign out">
              <LogOut size={14} />
            </button>
          )}
        </div>
      )}

      {/* Collapse toggle */}
      <button onClick={toggleSidebar}
        className="relative flex items-center justify-center py-3 border-t border-white/8 text-white/30 hover:text-white transition-colors">
        {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
      </button>
    </motion.aside>
  )
}
