import { useState } from 'react'
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

export default function App() {
  const { activePanel, isAuthenticated } = useKIPStore()

  // If already authenticated (persisted token), go straight to app
  const [screen, setScreen] = useState<Screen>(isAuthenticated ? 'app' : 'landing')

  if (screen === 'landing') return (
    <LandingPage
      onEnter={() => setScreen(isAuthenticated ? 'app' : 'auth')}
    />
  )

  if (screen === 'auth') return (
    <AuthPage
      onSuccess={() => setScreen('app')}
      onBack={() => setScreen('landing')}
    />
  )

  // ── Main app ──────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen bg-kip-navy font-body overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-hidden bg-kip-navy">
        {activePanel === 'chat'      && <ChatPanel />}
        {activePanel === 'dashboard' && <DashboardPanel />}
        {activePanel === 'news'      && <NewsPanel />}
        {activePanel === 'journey'   && <JourneyPanel />}
      </main>
    </div>
  )
}
