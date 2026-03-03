import axios from 'axios'
import { useKIPStore } from '@/store/kipStore'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({ baseURL: BASE })

// ── Attach auth token to every request ────────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = useKIPStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Auto-refresh on 401 ───────────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = useKIPStore.getState().refreshToken
      if (refresh) {
        try {
          const res = await axios.post(`${BASE}/auth/refresh`, { refresh_token: refresh })
          const { access_token, refresh_token } = res.data
          useKIPStore.getState().updateAccessToken(access_token)
          // Also update refresh token in store
          useKIPStore.setState({ refreshToken: refresh_token })
          original.headers.Authorization = `Bearer ${access_token}`
          return api(original)
        } catch {
          // Refresh failed — clear auth and redirect to login
          useKIPStore.getState().clearAuth()
          window.location.reload()
        }
      }
    }
    return Promise.reject(error)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authLogin = async (email: string, password: string) => {
  const res = await api.post('/auth/login', { email, password })
  return res.data
}

export const authRegister = async (name: string, email: string, password: string, location?: string) => {
  const res = await api.post('/auth/register', { name, email, password, location })
  return res.data
}

export const authLogout = async (refreshToken: string) => {
  await api.post('/auth/logout', { refresh_token: refreshToken })
}

export const getMe = async () => {
  const res = await api.get('/auth/me')
  return res.data
}

// ── News & Indicators ─────────────────────────────────────────────────────────
export const fetchNewsAndIndicators = async () => {
  const res = await api.get('/news/all')
  return res.data
}

export const fetchNews = async () => {
  const res = await api.get('/news/feed')
  return res.data
}

export const fetchIndicators = async () => {
  const res = await api.get('/news/indicators')
  return res.data
}

// ── Chat ──────────────────────────────────────────────────────────────────────
export const sendMessage = async (
  content: string,
  sessionToken: string,
  userId: number | null,
  businessId: number | null,
) => {
  const res = await api.post('/chat/message', {
    content, session_token: sessionToken, user_id: userId, business_id: businessId,
  })
  return res.data
}

export const getChatHistory = async (sessionToken: string) => {
  const res = await api.get(`/chat/history/${sessionToken}`)
  return res.data
}

export const getConversations = async () => {
  const res = await api.get('/chat/conversations')
  return res.data
}

export const startJourney = async (data: {
  conversation_id: number
  user_id: number
  business_name: string
  sector: string
  location: string
  start_capital: number
}) => {
  const res = await api.post('/chat/start-journey', data)
  return res.data
}

// ── Forecasts ─────────────────────────────────────────────────────────────────
export const getAllForecasts = async () => {
  const res = await api.get('/forecast/all')
  return res.data
}

// ── Business journey ──────────────────────────────────────────────────────────
export const getBusiness = async (businessId: number) => {
  const res = await api.get(`/business/${businessId}`)
  return res.data
}

export const addBusinessLog = async (businessId: number, data: any) => {
  const res = await api.post(`/business/${businessId}/log`, data)
  return res.data
}

export const getBusinessLogs = async (businessId: number) => {
  const res = await api.get(`/business/${businessId}/logs`)
  return res.data
}

export const getUserBusinesses = async (userId: number) => {
  const res = await api.get(`/users/${userId}/businesses`)
  return res.data
}
