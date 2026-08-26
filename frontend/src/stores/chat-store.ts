import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { createSafeStorage } from '../lib/safe-storage'
import * as api from '../api/client'
import type { Session, Message, StreamEvent, StreamFailure } from '../api/types'

export interface StreamDraft {
  content: string
  tools: string[]
  citations: any[]
  usage: any | null
}

const EMPTY_DRAFT: StreamDraft = { content: '', tools: [], citations: [], usage: null }

interface ChatState {
  // Backend State
  sessions: Session[]
  activeSessionId: string | null
  messages: Message[]
  
  // Ephemeral State
  isStreaming: boolean
  draft: StreamDraft | null
  failure: StreamFailure | null
  artifactId: string | null
  
  // Settings (Persisted)
  model: string
  systemPrompt: string
  temperature: number
  topP: number
  maxTokens: number
  veniceParams: any

  // Actions
  refreshSessions: () => Promise<void>
  selectSession: (id: string) => Promise<void>
  newSession: (provider?: string) => Promise<Session>
  send: (content: string, model: string, abortRef: React.MutableRefObject<AbortController | null>) => Promise<void>
  setArtifactId: (id: string | null) => void
  
  // Settings Actions
  setModel: (m: string) => void
  setSystemPrompt: (prompt: string) => void
  setTemperature: (t: number) => void
  setTopP: (p: number) => void
  setMaxTokens: (t: number) => void
  setVeniceParams: (params: any) => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      sessions: [],
      activeSessionId: null,
      messages: [],
      
      isStreaming: false,
      draft: null,
      failure: null,
      artifactId: null,
      
      model: 'claude-3-haiku-20240307',
      systemPrompt: '',
      temperature: 0.7,
      topP: 1,
      maxTokens: 4096,
      veniceParams: {},

      refreshSessions: async () => {
        try {
          const sessions = await api.listSessions()
          set({ sessions })
        } catch (e) {
          console.error("Failed to load sessions", e)
        }
      },

      selectSession: async (id: string) => {
        set({ activeSessionId: id, failure: null, artifactId: null })
        try {
          const messages = await api.listMessages(id)
          set({ messages })
        } catch (e) {
          console.error("Failed to load messages", e)
        }
      },

      newSession: async (provider?: string) => {
        const session = await api.createSession(provider)
        set((s) => ({
          sessions: [session, ...s.sessions],
          activeSessionId: session.id,
          messages: [],
          failure: null,
          artifactId: null
        }))
        return session
      },

      send: async (content: string, model: string, abortRef) => {
        let sessionId = get().activeSessionId
        if (!sessionId) {
          const session = await get().newSession(model)
          sessionId = session.id
        }
        
        set({ failure: null, isStreaming: true })
        
        // Optimistic user message
        set((s) => ({
          messages: [
            ...s.messages,
            {
              id: `optimistic-${Date.now()}`,
              role: "user",
              content,
              citations: [],
              artifact_id: null,
              usage: null,
              created_at: new Date().toISOString(),
            } as Message,
          ],
          draft: { ...EMPTY_DRAFT }
        }))

        const controller = new AbortController()
        abortRef.current = controller

        try {
          await api.streamMessage(
            sessionId,
            content,
            (event: StreamEvent) => {
              if (event.type === "token") {
                set((s) => ({ draft: s.draft ? { ...s.draft, content: s.draft.content + event.text } : null }))
              } else if (event.type === "tool_use") {
                set((s) => ({ draft: s.draft ? { ...s.draft, tools: [...s.draft.tools, `${event.tool}: ${event.summary}`] } : null }))
              } else if (event.type === "citation") {
                set((s) => ({ draft: s.draft ? { ...s.draft, citations: [...s.draft.citations, event.citation] } : null }))
              } else if (event.type === "artifact") {
                set({ artifactId: event.artifact_id })
              } else if (event.type === "done") {
                set((s) => ({ draft: s.draft ? { ...s.draft, usage: event.usage } : null }))
              } else if (event.type === "error") {
                set({ failure: event as StreamFailure })
              }
            },
            controller.signal
          )
        } catch (e) {
          const err = e as api.RequestError
          set({
            failure: {
              code: err.code ?? "network_error",
              message: err.message ?? "Connection lost.",
              recoverable: true,
            }
          })
        } finally {
          abortRef.current = null
          set({ isStreaming: false, draft: null })
          
          try {
            // Reload authoritative state
            const messages = await api.listMessages(sessionId)
            set({ messages })
            get().refreshSessions()
          } catch {
            // Backend down
          }
        }
      },

      setArtifactId: (id) => set({ artifactId: id }),
      
      setModel: (m) => set({ model: m }),
      setSystemPrompt: (prompt) => set({ systemPrompt: prompt }),
      setTemperature: (t) => set({ temperature: t }),
      setTopP: (p) => set({ topP: p }),
      setMaxTokens: (t) => set({ maxTokens: t }),
      setVeniceParams: (params) => set((s) => ({ veniceParams: { ...s.veniceParams, ...params } })),
    }),
    {
      name: 'lenny-chat-settings',
      storage: createJSONStorage(() => createSafeStorage()),
      partialize: (state) => ({
        model: state.model,
        systemPrompt: state.systemPrompt,
        temperature: state.temperature,
        topP: state.topP,
        maxTokens: state.maxTokens,
        veniceParams: state.veniceParams,
      }),
    }
  )
)
