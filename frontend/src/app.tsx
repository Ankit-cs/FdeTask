import { useState, useEffect } from 'react'
import { useSettingsStore, type Tab } from './stores/settings-store'
import { useChatStore } from './stores/chat-store'
import { useAuthStore } from './stores/auth-store'
import { Sidebar } from './components/layout/sidebar'
import { Header } from './components/layout/header'
import { ApiKeyDialog } from './components/layout/api-key-dialog'
import { ChatView } from './components/chat/chat-view'
import { ErrorBoundary } from './components/ui/error-boundary'
import { Toaster } from './components/ui/toaster'
import ArtifactViewer from './components/chat/ArtifactViewer'

const views = {
  chat: ChatView,
} as const

const TAB_ORDER: Tab[] = ['chat']

export function App() {
  const needsUnlock = useAuthStore((s) => s.hasEncrypted && !s.apiKey)
  const [apiKeyOpen, setApiKeyOpen] = useState(needsUnlock)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const activeTab = useSettingsStore((s) => s.activeTab)
  const setActiveTab = useSettingsStore((s) => s.setActiveTab)
  const ActiveView = views[activeTab]
  
  const artifactId = useChatStore((s) => s.artifactId)
  const setArtifactId = useChatStore((s) => s.setArtifactId)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isMeta = e.metaKey || e.ctrlKey
      if (!isMeta) return

      if (e.key === 'n') {
        e.preventDefault()
        setActiveTab('chat')
        setMobileSidebarOpen(false)
        useChatStore.getState().newSession()
        return
      }

      const num = parseInt(e.key, 10)
      if (num >= 1 && num <= TAB_ORDER.length) {
        e.preventDefault()
        setActiveTab(TAB_ORDER[num - 1])
        setMobileSidebarOpen(false)
        return
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [setActiveTab])

  return (
    <div className="flex h-[100dvh] w-screen overflow-hidden">
      {/* Mobile drawer overlay */}
      {mobileSidebarOpen && (
        <button
          aria-label="Close menu"
          className="md:hidden fixed inset-0 z-30 bg-black/60 backdrop-blur-sm animate-fade-in"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}
      <Sidebar mobileOpen={mobileSidebarOpen} onMobileClose={() => setMobileSidebarOpen(false)} />
      <div className="flex flex-col flex-1 min-w-0">
        <Header
          onOpenApiKey={() => setApiKeyOpen(true)}
          onOpenMobileSidebar={() => setMobileSidebarOpen(true)}
        />
        <main className="flex-1 min-h-0 overflow-hidden relative flex">
          <ErrorBoundary key={activeTab}>
            <div className="flex-1 min-w-0 relative">
              <ActiveView />
            </div>
            {artifactId && (
              <ArtifactViewer artifactId={artifactId} onClose={() => setArtifactId(null)} />
            )}
          </ErrorBoundary>
        </main>
      </div>
      <ApiKeyDialog open={apiKeyOpen} onClose={() => setApiKeyOpen(false)} />
      <Toaster />
    </div>
  )
}
