import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Cpu, Mail, Lock, User, MapPin, ArrowRight, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { useKIPStore } from '@/store/kipStore'
import { authLogin, authRegister } from '@/hooks/useAPI'

interface Props { onSuccess: () => void; onBack: () => void }

export default function AuthPage({ onSuccess, onBack }: Props) {
  const [tab, setTab]         = useState<'login' | 'register'>('login')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [showPwd, setShowPwd] = useState(false)

  const [form, setForm] = useState({
    name: '', email: '', password: '', location: '',
  })

  const { setAuth } = useKIPStore()

  const f = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  const handleSubmit = async () => {
    setError('')
    if (!form.email || !form.password) { setError('Email and password are required.'); return }
    if (tab === 'register' && !form.name.trim()) { setError('Please enter your name.'); return }
    if (form.password.length < 6) { setError('Password must be at least 6 characters.'); return }

    setLoading(true)
    try {
      const result = tab === 'login'
        ? await authLogin(form.email, form.password)
        : await authRegister(form.name, form.email, form.password, form.location)

      setAuth(result.access_token, result.refresh_token, result.user)
      onSuccess()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSubmit()
  }

  return (
    <div className="fixed inset-0 flex items-center justify-center p-4"
      style={{ background: 'linear-gradient(135deg, #0A1628 0%, #0D1F3C 100%)' }}>
      <div className="neural-overlay absolute inset-0 pointer-events-none" />

      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
        className="relative z-10 w-full max-w-md">

        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-kip-navymid border border-kip-cornflower/30 flex items-center justify-center mb-3 shadow-glow">
            <Cpu size={28} className="text-kip-cornflower" />
          </div>
          <h1 className="font-display font-bold text-2xl text-white">Welcome to KIP</h1>
          <p className="font-body text-sm text-white/40 mt-1">Kwacha Intelligence Platform</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-kip-navylight overflow-hidden"
          style={{ background: 'rgba(13,31,60,0.95)', backdropFilter: 'blur(16px)' }}>

          {/* Tabs */}
          <div className="flex border-b border-kip-navylight">
            {(['login', 'register'] as const).map(t => (
              <button key={t} onClick={() => { setTab(t); setError('') }}
                className={`flex-1 py-3.5 text-sm font-body font-semibold transition-all ${
                  tab === t
                    ? 'text-white border-b-2 border-kip-cornflower bg-kip-cornflower/5'
                    : 'text-white/40 hover:text-white/70'
                }`}>
                {t === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          <div className="p-6">
            <AnimatePresence mode="wait">
              <motion.div key={tab} initial={{ opacity: 0, x: tab === 'login' ? -12 : 12 }}
                animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>

                {/* Error */}
                {error && (
                  <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 mb-4">
                    <AlertCircle size={14} className="text-red-400 flex-shrink-0" />
                    <p className="text-sm font-body text-red-400">{error}</p>
                  </motion.div>
                )}

                <div className="space-y-3">
                  {/* Name (register only) */}
                  {tab === 'register' && (
                    <InputField icon={<User size={15}/>} placeholder="Full name"
                      value={form.name} onChange={f('name')} onKeyDown={handleKey} />
                  )}

                  {/* Email */}
                  <InputField icon={<Mail size={15}/>} placeholder="Email address" type="email"
                    value={form.email} onChange={f('email')} onKeyDown={handleKey} />

                  {/* Password */}
                  <div className="relative">
                    <InputField icon={<Lock size={15}/>}
                      placeholder={tab === 'login' ? 'Password' : 'Password (min. 6 chars)'}
                      type={showPwd ? 'text' : 'password'}
                      value={form.password} onChange={f('password')} onKeyDown={handleKey} />
                    <button onClick={() => setShowPwd(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors">
                      {showPwd ? <EyeOff size={15}/> : <Eye size={15}/>}
                    </button>
                  </div>

                  {/* Location (register only) */}
                  {tab === 'register' && (
                    <InputField icon={<MapPin size={15}/>} placeholder="Your city/town (e.g. Lusaka)"
                      value={form.location} onChange={f('location')} onKeyDown={handleKey} />
                  )}
                </div>

                {/* Submit */}
                <motion.button onClick={handleSubmit} disabled={loading}
                  whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
                  className="w-full mt-5 py-3.5 rounded-xl font-body font-bold text-white flex items-center justify-center gap-2
                             disabled:opacity-50 transition-all group"
                  style={{ background: 'linear-gradient(135deg, #4A7BD4, #6495ED)' }}>
                  {loading
                    ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/> Verifying...</>
                    : <>{tab === 'login' ? 'Sign In to KIP' : 'Create My Account'}<ArrowRight size={16} className="group-hover:translate-x-1 transition-transform"/></>
                  }
                </motion.button>

                {tab === 'login' && (
                  <p className="text-center text-xs text-white/30 font-body mt-3">
                    Don't have an account?{' '}
                    <button onClick={() => setTab('register')} className="text-kip-cornflower hover:underline">
                      Create one free
                    </button>
                  </p>
                )}
                {tab === 'register' && (
                  <p className="text-center text-xs text-white/30 font-body mt-3">
                    Already have an account?{' '}
                    <button onClick={() => setTab('login')} className="text-kip-cornflower hover:underline">
                      Sign in
                    </button>
                  </p>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* Back to news */}
        <button onClick={onBack} className="w-full text-center mt-4 text-xs text-white/25 hover:text-white/50 font-body transition-colors">
          ← Back to Zambia Intelligence
        </button>
      </motion.div>
    </div>
  )
}

function InputField({ icon, value, onChange, onKeyDown, placeholder, type = 'text' }: any) {
  return (
    <div className="flex items-center gap-3 bg-kip-navylight/60 border border-kip-navylight rounded-xl px-4 py-3
                    focus-within:border-kip-cornflower/50 focus-within:bg-kip-navylight transition-all">
      <span className="text-white/30 flex-shrink-0">{icon}</span>
      <input type={type} placeholder={placeholder} value={value}
        onChange={onChange} onKeyDown={onKeyDown}
        className="flex-1 bg-transparent text-white placeholder-white/25 text-sm font-body outline-none" />
    </div>
  )
}
