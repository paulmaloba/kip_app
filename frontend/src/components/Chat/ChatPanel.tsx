import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, Cpu, User } from 'lucide-react'
import { useKIPStore } from '@/store/kipStore'
import { sendMessage } from '@/hooks/useAPI'
import { ResponseRouter } from '@/components/ResponseLayouts'
import { ChatMessage } from '@/types'

const SUGGESTIONS = [
  "What business can I start with K10,000 in Lusaka?",
  "Explain Zambia's current inflation and what it means for my shop",
  "How do I register a food business with ZABS?",
  "My supplier hasn't delivered and I can't pay rent — help",
]

export default function ChatPanel() {
  const [input, setInput] = useState('')
  const bottomRef         = useRef<HTMLDivElement>(null)
  const textareaRef       = useRef<HTMLTextAreaElement>(null)

  const {
    messages, isLoading, sessionToken, userId, activeBusiness,
    conversationId, addUserMessage, addAssistantMessage,
    setLoading, setConversationId,
  } = useKIPStore()

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, isLoading])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return
    const text = input.trim()
    setInput('')
    addUserMessage(text)
    setLoading(true)
    try {
      const resp = await sendMessage(text, sessionToken, userId, activeBusiness?.id || null)
      if (resp.conversation_id && !conversationId) setConversationId(resp.conversation_id)
      addAssistantMessage(resp.message_id, {
        content: resp.content, response_type: resp.response_type, structured: resp.structured,
      })
    } catch (err: any) {
      addAssistantMessage('err-' + Date.now(), {
        content: `KIP is temporarily unavailable. ${err?.response?.data?.detail || err.message || ''}`,
        response_type: 'general',
      })
    }
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div className="flex flex-col h-full bg-kip-navy">
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 bg-kip-navy">
        {messages.length === 0 && <WelcomeScreen onSuggestion={(s) => { setInput(s); textareaRef.current?.focus() }} />}
        <AnimatePresence>
          {messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)}
        </AnimatePresence>
        {isLoading && <ThinkingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-kip-navylight bg-kip-navymid px-4 py-4">
        <div className="flex items-end gap-3 max-w-3xl mx-auto">
          <div className="flex-1">

               <textarea
                  style={{ color: '#ffffff', caretColor: '#6495ED', minHeight: '48px' }}
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder="Ask KIP anything about business in Zambia..."
                  rows={1}
                  className="w-full resize-none rounded-xl border border-kip-light bg-kip-offwhite
                             px-4 py-3 font-body text-sm text-kip-charcoal placeholder-kip-muted
                             focus:outline-none focus:ring-2 focus:ring-kip-cornflower/30
                             focus:border-kip-cornflower/50 transition-all max-h-32 overflow-y-auto bg-kip-navylight text-white placeholder-white/30 border-kip-navylight"
                  onInput={(e) => {
                    const t = e.target as HTMLTextAreaElement
                    t.style.height = 'auto'
                    t.style.height = Math.min(t.scrollHeight, 128) + 'px'
                  }}
                />
          </div>
          <motion.button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            className="flex-shrink-0 w-11 h-11 rounded-xl bg-kip-cornflower flex items-center justify-center
                       text-white disabled:opacity-40 disabled:cursor-not-allowed
                       hover:bg-kip-cornflowerdark transition-colors shadow-navy"
          >
            {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </motion.button>
        </div>
        <p className="text-center text-xs text-white/25 font-body mt-2">
          KIP uses AI — verify important decisions with a professional.
        </p>
      </div>
    </div>
  )
}

function WelcomeScreen({ onSuggestion }: { onSuggestion: (s: string) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-12 text-center max-w-lg mx-auto"
    >
      <div className="w-16 h-16 rounded-2xl bg-kip-gradient flex items-center justify-center mb-4 shadow-glow neural-overlay">
        <Cpu className="text-kip-cornflower" size={28} />
      </div>
      <h2 className="font-display font-bold text-2xl text-white mb-2">Good day. I'm KIP.</h2>
      <p className="font-body text-sm text-white/50 mb-8 leading-relaxed">
        Your Zambian business intelligence partner. Ask me about starting a business,
        understanding the economy, navigating regulations, or handling a crisis.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full">
        {SUGGESTIONS.map((s, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.08 }}
            onClick={() => onSuggestion(s)}
            className="text-left px-4 py-3 rounded-xl border border-kip-navylight bg-kip-navymid
                       hover:bg-kip-navylight hover:border-kip-cornflower/40
                       text-sm font-body text-white/70 transition-all hover:shadow-sm"
          >
            {s}
          </motion.button>
        ))}
      </div>
    </motion.div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-start gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-kip-gradient flex items-center justify-center flex-shrink-0 mt-0.5 shadow-navy">
          <Cpu size={14} className="text-kip-cornflower" />
        </div>
      )}
      <div className={`max-w-2xl flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        {isUser ? (
          <div className="bg-kip-navy text-white rounded-2xl rounded-tr-sm px-4 py-3 font-body text-sm shadow-navy">
            {message.content}
          </div>
        ) : (
          <div className="w-full">
            <ResponseRouter
              responseType={message.response_type || 'general'}
              content={message.content}
              structured={message.structured}
            />
          </div>
        )}
        <span className="text-xs text-kip-muted font-mono mt-1 px-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          {message.response_type && message.response_type !== 'general' && !isUser && (
            <span className="ml-2 text-kip-cornflower">[{message.response_type.replace('_', ' ')}]</span>
          )}
        </span>
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-kip-light flex items-center justify-center flex-shrink-0 mt-0.5">
          <User size={14} className="text-kip-muted" />
        </div>
      )}
    </motion.div>
  )
}

function ThinkingIndicator() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3">
      <div className="w-8 h-8 rounded-xl bg-kip-gradient flex items-center justify-center flex-shrink-0 shadow-navy">
        <Cpu size={14} className="text-kip-cornflower" />
      </div>
      <div className="bg-kip-navymid border border-kip-navylight rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex gap-1.5 items-center">
          {[0, 150, 300].map((delay) => (
            <div key={delay} className="w-1.5 h-1.5 rounded-full bg-kip-cornflower animate-bounce" style={{ animationDelay: `${delay}ms` }} />
          ))}
          <span className="text-xs font-body text-white/40 ml-2">KIP is thinking...</span>
        </div>
      </div>
    </motion.div>
  )
}
