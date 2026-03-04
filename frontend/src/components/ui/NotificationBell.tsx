import { useState, useEffect, useRef } from 'react'
import { Bell, X, TrendingUp, TrendingDown, AlertTriangle, Info, CheckCheck } from 'lucide-react'
import { useKIPStore } from '@/store/kipStore'
import axios from 'axios'

const BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api'

interface Notification {
  id:           string
  title:        string
  message:      string
  type:         'info' | 'warning' | 'alert' | 'success'
  created_at:   string
  read:         boolean
  action_label?: string
  action_url?:  string
  data?:        any
}

const TYPE_STYLES = {
  alert:   { bg: 'bg-red-500/15',    border: 'border-red-500/30',    icon: AlertTriangle, color: 'text-red-400' },
  warning: { bg: 'bg-amber-500/15',  border: 'border-amber-500/30',  icon: TrendingDown,  color: 'text-amber-400' },
  success: { bg: 'bg-green-500/15',  border: 'border-green-500/30',  icon: TrendingUp,    color: 'text-green-400' },
  info:    { bg: 'bg-blue-500/15',   border: 'border-blue-500/30',   icon: Info,          color: 'text-blue-400' },
}

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)   return 'just now'
  if (mins < 60)  return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)   return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function NotificationBell() {
  const { user } = useKIPStore()
  const [open,          setOpen]          = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unread,        setUnread]        = useState(0)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const fetchNotifications = async () => {
    if (!user?.id) return
    try {
      const { data } = await axios.get(`${BASE}/notifications?user_id=${user.id}`)
      setNotifications(data.notifications || [])
      setUnread(data.unread || 0)
    } catch { /* silent */ }
  }

  // Poll every 60 seconds for new notifications
  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(fetchNotifications, 60000)
    return () => clearInterval(interval)
  }, [user?.id])

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const markAllRead = async () => {
    if (!user?.id) return
    try {
      await axios.post(`${BASE}/notifications/read`, null, {
        params: { user_id: user.id }
      })
      setNotifications(prev => prev.map(n => ({ ...n, read: true })))
      setUnread(0)
    } catch { /* silent */ }
  }

  const markOneRead = async (id: string) => {
    if (!user?.id) return
    try {
      await axios.post(`${BASE}/notifications/read`, null, {
        params: { user_id: user.id, notification_id: id }
      })
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n))
      setUnread(prev => Math.max(0, prev - 1))
    } catch { /* silent */ }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell button */}
      <button
        onClick={() => { setOpen(o => !o); if (!open) fetchNotifications() }}
        className="relative flex items-center justify-center w-9 h-9 rounded-xl
                   text-white/40 hover:text-white hover:bg-white/8 transition-colors"
        title="Notifications"
      >
        <Bell size={18} />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1
                           bg-red-500 text-white text-[10px] font-bold rounded-full
                           flex items-center justify-center animate-pulse">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-11 w-80 z-50 rounded-2xl shadow-2xl overflow-hidden
                        border border-white/10"
             style={{ background: '#0D1F3C' }}>

          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/8">
            <div>
              <p className="font-body font-bold text-white text-sm">Notifications</p>
              {unread > 0 && (
                <p className="font-body text-kip-cornflower text-xs">{unread} unread</p>
              )}
            </div>
            <div className="flex items-center gap-2">
              {unread > 0 && (
                <button onClick={markAllRead}
                  className="text-white/30 hover:text-kip-cornflower transition-colors"
                  title="Mark all read">
                  <CheckCheck size={16} />
                </button>
              )}
              <button onClick={() => setOpen(false)}
                className="text-white/30 hover:text-white transition-colors">
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Notification list */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <Bell size={28} className="text-white/15 mx-auto mb-2" />
                <p className="font-body text-white/30 text-sm">No notifications yet</p>
                <p className="font-body text-white/20 text-xs mt-1">
                  KIP will alert you when exchange rates move significantly
                </p>
              </div>
            ) : (
              notifications.map((notif) => {
                const style = TYPE_STYLES[notif.type] || TYPE_STYLES.info
                const Icon  = style.icon
                return (
                  <div key={notif.id}
                    onClick={() => markOneRead(notif.id)}
                    className={`px-4 py-3 border-b border-white/5 cursor-pointer
                                transition-colors hover:bg-white/5
                                ${!notif.read ? 'border-l-2 border-l-kip-cornflower' : ''}`}>
                    <div className="flex gap-3">
                      <div className={`mt-0.5 p-1.5 rounded-lg flex-shrink-0 ${style.bg} ${style.border} border`}>
                        <Icon size={12} className={style.color} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <p className={`font-body font-bold text-xs ${!notif.read ? 'text-white' : 'text-white/70'}`}>
                            {notif.title}
                          </p>
                          <span className="font-mono text-white/25 text-[10px] flex-shrink-0">
                            {timeAgo(notif.created_at)}
                          </span>
                        </div>
                        <p className="font-body text-white/50 text-xs mt-0.5 leading-relaxed">
                          {notif.message.split('\n')[0]}
                        </p>
                        {notif.message.includes('\n') && (
                          <p className="font-body text-kip-cornflower/60 text-[10px] mt-1">
                            {notif.message.split('\n')[1]}
                          </p>
                        )}
                        {!notif.read && (
                          <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-kip-cornflower" />
                        )}
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>

          {notifications.length > 0 && (
            <div className="px-4 py-2 border-t border-white/8">
              <p className="font-body text-white/20 text-[10px] text-center">
                Rate alerts update every hour • Major moves trigger instant alerts
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
