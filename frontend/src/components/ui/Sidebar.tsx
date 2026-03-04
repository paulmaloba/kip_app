import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, BarChart2, Briefcase, ChevronLeft, ChevronRight, Cpu, Globe, LogOut, User, X } from 'lucide-react'
import { useKIPStore } from '@/store/kipStore'
import { authLogout } from '@/hooks/useAPI'
import NotificationBell from '@/components/ui/NotificationBell'

const NAV_ITEMS = [
  { id: 'chat',      label: 'Ask KIP',     icon: MessageSquare, desc: 'Business intelligence' },
  { id: 'dashboard', label: 'Economy',     icon: BarChart2,     desc: 'Forecasts & indicators' },
  { id: 'news',      label: 'ZM News',     icon: Globe,         desc: 'Live Zambian updates' },
  { id: 'journey',   label: 'My Business', icon: Briefcase,     desc: 'Track your journey' },
] as const

interface Props {
  mobileOpen?: boolean
  onMobileClose?: () => void
}

export default function Sidebar({ mobileOpen = false, onMobileClose }: Props) {
  const { sidebarOpen, toggleSidebar, activePanel, setActivePanel, activeBusiness, user, refreshToken, clearAuth } = useKIPStore()

  const handleLogout = async () => {
    try { if (refreshToken) await authLogout(refreshToken) } finally { clearAuth() }
  }

  const handleNav = (id: typeof NAV_ITEMS[number]['id']) => {
    setActivePanel(id)
    onMobileClose?.()
  }

  const Inner = ({ collapsed }: { collapsed: boolean }) => (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/8">
        <div className="w-9 h-9 rounded-xl bg-kip-cornflower/20 border border-kip-cornflower/40 flex items-center justify-center flex-shrink-0">
          <Cpu size={18} className="text-kip-cornflower" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="font-display font-bold text-white text-lg leading-none">KIP</div>
              <div className="font-body text-kip-cornflower/60 text-[10px] tracking-widest uppercase mt-0.5">Kwacha Intelligence</div>
            </motion.div>
          )}
        </AnimatePresence>
        {!collapsed && (
        <div className="ml-auto">
          <NotificationBell />
        </div>
        )}
        {onMobileClose && (
          <button onClick={onMobileClose} className="ml-auto text-white/40 hover:text-white transition-colors">
            <X size={18} />
          </button>
        )}
      </div>

      <nav className="flex-1 px-2 py-4 space-y-1">
        {NAV_ITEMS.map(({ id, label, icon: Icon, desc }) => {
          const active = activePanel === id
          return (
            <button key={id} onClick={() => handleNav(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left ${
                active ? 'bg-kip-cornflower text-white' : 'text-white/40 hover:text-white hover:bg-white/8'
              }`}>
              <Icon size={18} className="flex-shrink-0" />
              {!collapsed && (
                <div>
                  <div className="font-body font-semibold text-sm">{label}</div>
                  <div className={`font-body text-[10px] ${active ? 'text-white/70' : 'text-white/30'}`}>{desc}</div>
                </div>
              )}
            </button>
          )
        })}
      </nav>

      {activeBusiness && !collapsed && (
        <div className="mx-2 mb-2 p-3 rounded-xl bg-kip-cornflower/15 border border-kip-cornflower/30">
          <p className="font-body text-[10px] text-kip-cornflower/70 uppercase tracking-widest mb-0.5">Active Journey</p>
          <p className="font-body font-semibold text-white text-xs truncate">{activeBusiness.name}</p>
        </div>
      )}

      {user && (
        <div className={`border-t border-white/8 px-3 py-3 flex items-center gap-2 ${collapsed ? 'justify-center' : ''}`}>
          <div className="w-7 h-7 rounded-lg bg-kip-cornflower/20 flex items-center justify-center flex-shrink-0">
            <User size={13} className="text-kip-cornflower" />
          </div>
          {!collapsed && <>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-body font-semibold text-white truncate">{user.name}</p>
              <p className="text-[10px] font-mono text-white/30 truncate">{user.email}</p>
            </div>
            <button onClick={handleLogout} className="text-white/25 hover:text-red-400 transition-colors" title="Sign out">
              <LogOut size={14} />
            </button>
          </>}
        </div>
      )}

      {!onMobileClose && (
        <button onClick={toggleSidebar}
          className="flex items-center justify-center py-3 border-t border-white/8 text-white/30 hover:text-white transition-colors">
          {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>
      )}
    </div>
  )

  return (
    <>
      {/* Desktop sidebar — hidden on mobile */}
      <motion.aside animate={{ width: sidebarOpen ? 224 : 64 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="hidden md:flex flex-col h-full overflow-hidden relative z-10"
        style={{ background: 'linear-gradient(180deg, #0A1628 0%, #0D1F3C 100%)' }}>
        <div className="absolute inset-0 neural-overlay pointer-events-none" />
        <div className="relative flex flex-col h-full"><Inner collapsed={!sidebarOpen} /></div>
      </motion.aside>

      {/* Mobile drawer overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={onMobileClose} className="md:hidden fixed inset-0 bg-black/60 z-40" />
            <motion.div initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="md:hidden fixed left-0 top-0 bottom-0 w-64 z-50 flex flex-col"
              style={{ background: 'linear-gradient(180deg, #0A1628 0%, #0D1F3C 100%)' }}>
              <Inner collapsed={false} />
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
