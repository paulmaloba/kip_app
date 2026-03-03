import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { ChatMessage, BusinessProfile, ForecastData, DashboardMetrics, CPIIndicator, KIPUser } from '@/types'

interface KIPStore {
  // ── Auth ────────────────────────────────────────────────────────────────────
  user:          KIPUser | null
  accessToken:   string | null
  refreshToken:  string | null
  isAuthenticated: boolean
  setAuth:       (access: string, refresh: string, user: KIPUser) => void
  clearAuth:     () => void
  updateAccessToken: (token: string) => void

  // ── Session ─────────────────────────────────────────────────────────────────
  sessionToken:    string
  userId:          number | null
  conversationId:  number | null
  setConversationId: (id: number) => void

  // ── Chat ────────────────────────────────────────────────────────────────────
  messages:    ChatMessage[]
  isLoading:   boolean
  addUserMessage:      (content: string) => void
  addAssistantMessage: (id: string, data: { content: string; response_type?: string; structured?: any }) => void
  setLoading:  (v: boolean) => void
  clearMessages: () => void

  // ── Business journey ────────────────────────────────────────────────────────
  activeBusiness: BusinessProfile | null
  setActiveBusiness: (b: BusinessProfile | null) => void

  // ── Dashboard ───────────────────────────────────────────────────────────────
  metrics:            DashboardMetrics | null
  gdpForecast:        ForecastData | null
  inflationForecast:  ForecastData | null
  cpiIndicators:      CPIIndicator[]
  setDashboardData:   (data: { metrics: DashboardMetrics; gdp: ForecastData; inflation: ForecastData; cpi: CPIIndicator[] }) => void

  // ── UI ──────────────────────────────────────────────────────────────────────
  activePanel:   'chat' | 'dashboard' | 'journey' | 'news'
  sidebarOpen:   boolean
  setActivePanel: (p: 'chat' | 'dashboard' | 'journey' | 'news') => void
  toggleSidebar:  () => void
}

function genSessionToken(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export const useKIPStore = create<KIPStore>()(
  persist(
    (set, get) => ({
      // ── Auth ──────────────────────────────────────────────────────────────
      user:            null,
      accessToken:     null,
      refreshToken:    null,
      isAuthenticated: false,

      setAuth: (access, refresh, user) => set({
        accessToken:     access,
        refreshToken:    refresh,
        user,
        isAuthenticated: true,
        userId:          user.id,
      }),

      clearAuth: () => set({
        accessToken:     null,
        refreshToken:    null,
        user:            null,
        isAuthenticated: false,
        userId:          null,
        messages:        [],
        conversationId:  null,
        activeBusiness:  null,
      }),

      updateAccessToken: (token) => set({ accessToken: token }),

      // ── Session ────────────────────────────────────────────────────────────
      sessionToken:   genSessionToken(),
      userId:         null,
      conversationId: null,
      setConversationId: (id) => set({ conversationId: id }),

      // ── Chat ───────────────────────────────────────────────────────────────
      messages:  [],
      isLoading: false,

      addUserMessage: (content) => set(state => ({
        messages: [...state.messages, {
          id:        'u-' + Date.now(),
          role:      'user',
          content,
          timestamp: new Date(),
        }],
      })),

      addAssistantMessage: (id, data) => set(state => ({
        messages: [...state.messages, {
          id,
          role:          'assistant',
          content:       data.content,
          response_type: data.response_type as any,
          structured:    data.structured,
          timestamp:     new Date(),
        }],
        isLoading: false,
      })),

      setLoading:    (v) => set({ isLoading: v }),
      clearMessages: ()  => set({ messages: [], conversationId: null }),

      // ── Business ───────────────────────────────────────────────────────────
      activeBusiness:    null,
      setActiveBusiness: (b) => set({ activeBusiness: b }),

      // ── Dashboard ──────────────────────────────────────────────────────────
      metrics:           null,
      gdpForecast:       null,
      inflationForecast: null,
      cpiIndicators:     [],

      setDashboardData: ({ metrics, gdp, inflation, cpi }) => set({
        metrics,
        gdpForecast:       gdp,
        inflationForecast: inflation,
        cpiIndicators:     cpi,
      }),

      // ── UI ─────────────────────────────────────────────────────────────────
      activePanel:   'chat',
      sidebarOpen:   true,
      setActivePanel: (p) => set({ activePanel: p }),
      toggleSidebar:  ()  => set(state => ({ sidebarOpen: !state.sidebarOpen })),
    }),
    {
      name:    'kip-store',
      // Only persist auth tokens and user — not messages or UI state
      partialize: (state) => ({
        accessToken:     state.accessToken,
        refreshToken:    state.refreshToken,
        user:            state.user,
        isAuthenticated: state.isAuthenticated,
        userId:          state.userId,
      }),
    }
  )
)
