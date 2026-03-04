import NotificationBell from '@/components/ui/NotificationBell'
import { useState } from 'react'
import { Menu, MessageSquare, BarChart2, Briefcase, Globe } from 'lucide-react'
import { useKIPStore } from '@/store/kipStore'
import Sidebar from '@/components/ui/Sidebar'
import ChatPanel from '@/components/Chat/ChatPanel'
import DashboardPanel from '@/components/Dashboard/DashboardPanel'
import JourneyPanel from '@/components/Dashboard/JourneyPanel'
import NewsPanel from '@/components/News/NewsPanel'
import LandingPage from '@/components/LandingPage'
import AuthPage from '@/components/Auth/AuthPage'
import '@/styles/global.css'

type Screen = 'landing' | 'auth' | 'app'

const MOBILE_NAV = [
  { id: 'chat',      label: 'Ask KIP',  icon: MessageSquare },
  { id: 'dashboard', label: 'Economy',  icon: BarChart2 },
  { id: 'news',      label: 'News',     icon: Globe },
  { id: 'journey',   label: 'Business', icon: Briefcase },
] as const

export default function App() {
  const { activePanel, setActivePanel, isAuthenticated } = useKIPStore()
  const [screen, setScreen] = useState<Screen>(isAuthenticated ? 'app' : 'landing')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  if (screen === 'landing') return (
    <LandingPage onEnter={() => setScreen(isAuthenticated ? 'app' : 'auth')} />
  )
  if (screen === 'auth') return (
    <AuthPage onSuccess={() => setScreen('app')} onBack={() => setScreen('landing')} />
  )

  return (
    <div className="flex h-screen bg-kip-navy overflow-hidden">
      {/* Desktop sidebar */}
      <Sidebar mobileOpen={mobileNavOpen} onMobileClose={() => setMobileNavOpen(false)} />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile top bar */}
        <div className="md:hidden flex items-center gap-3 px-4 py-3 border-b border-kip-navylight"
          style={{ background: '#0A1628' }}>
          <button onClick={() => setMobileNavOpen(true)}
            className="text-white/60 hover:text-white transition-colors">
            <Menu size={22} />
          </button>
          <span className="font-display font-bold text-white text-base">KIP</span>
          <span className="font-body text-kip-cornflower/60 text-xs">Kwacha Intelligence</span>
          <div className="ml-auto">
              <NotificationBell />
          </div>
        </div>

        {/* Main content */}
        <main className="flex-1 overflow-hidden">
          {activePanel === 'chat'      && <ChatPanel />}
          {activePanel === 'dashboard' && <DashboardPanel />}
          {activePanel === 'news'      && <NewsPanel />}
          {activePanel === 'journey'   && <JourneyPanel />}
        </main>

        {/* Mobile bottom nav */}
        <div className="md:hidden flex border-t border-kip-navylight"
          style={{ background: '#0A1628' }}>
          {MOBILE_NAV.map(({ id, label, icon: Icon }) => {
            const active = activePanel === id
            return (
              <button key={id} onClick={() => setActivePanel(id)}
                className={`flex-1 flex flex-col items-center gap-1 py-2.5 transition-colors ${
                  active ? 'text-kip-cornflower' : 'text-white/30'
                }`}>
                <Icon size={20} />
                <span className="text-[10px] font-body font-semibold">{label}</span>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
