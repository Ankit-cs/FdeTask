import { useEffect, useRef, useState } from 'react'
import { useChatStore } from '../../stores/chat-store'
import { useSettingsStore } from '../../stores/settings-store'
import { MessageBubble } from './message-bubble'
import { ChatInput } from './chat-input'
import { VeniceParams } from './venice-params'

const STARTER_PROMPTS = [
  'How did Airbnb solve the chicken-and-egg problem in their early days?',
  'What are the key differences between a growth loop and a traditional funnel?',
  'What are some effective retention strategies for a B2B SaaS product?',
  'Write a Ship 30 essay on the importance of finding product-market fit.',
]

export function ChatView() {
  const { messages, activeSessionId, isStreaming, send, draft, model } = useChatStore()
  
  const abortRef = useRef<AbortController | null>(null)
  
  const handleSend = (content: string) => {
    send(content, model, abortRef)
  }
  
  const stop = () => {
    if (abortRef.current) abortRef.current.abort()
  }

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const messageCount = messages.length ?? 0
  const scrollTrigger = `${messageCount}-${isStreaming}`
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [scrollTrigger, draft])

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-6 gap-6">
            <div className="flex flex-col items-center gap-3">
              <div className="text-[28px] font-serif font-semibold text-white/90">The Lenny Growth Assistant</div>
              <p className="text-[14px] text-white/50 max-w-md font-sans">
                A local-first, grounded assistant for exploring Lenny's Podcast transcripts. Ask about product, growth, or ask for a Ship 30 essay.
              </p>
            </div>
            <div className="w-full max-w-md flex flex-col gap-2 mt-4">
              <div className="text-[11px] uppercase tracking-[0.1em] text-white/40 font-semibold text-left">On Air: Popular Questions</div>
              <div className="flex flex-col gap-2">
                {STARTER_PROMPTS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => handleSend(p)}
                    className="text-left px-4 py-3 rounded-xl border border-white/[0.08] bg-white/[0.03] hover:border-white/[0.2] hover:bg-white/[0.06] transition-all duration-200 text-[14px] text-white/75 shadow-sm"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="w-full max-w-[960px] mx-auto py-5 px-4 sm:px-5 flex flex-col gap-5">
            {messages.map((msg, i) => (
              <MessageBubble
                key={i}
                message={msg}
                index={i}
                onCopy={() => {}}
                onDelete={() => {}}
                onRegenerate={undefined}
              />
            ))}
            {draft && (
              <MessageBubble
                key="draft"
                message={{ role: 'assistant', content: draft.content, citations: draft.citations }}
                index={messages.length}
                onCopy={() => {}}
                onDelete={() => {}}
                onRegenerate={undefined}
              />
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      <ChatInput onSend={(msg) => handleSend(msg)} onStop={stop} isStreaming={isStreaming} disabled={false} />
    </div>
  )
}
