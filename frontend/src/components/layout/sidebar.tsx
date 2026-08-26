import { useMemo, useState } from 'react'
import { cn } from '../../lib/utils'
import { useSettingsStore, type Tab } from '../../stores/settings-store'
import { useChatStore } from '../../stores/chat-store'
import { toast } from '../../stores/toast-store'
import { VeniceWordmark } from '../ui/logo'
import type { Session } from '../../api/types'

function ChatIcon() {
  return (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" /></svg>)
}

interface NavGroup {
  label: string
  items: Array<{ id: Tab; label: string; Icon: () => React.JSX.Element }>
}

const navGroups: NavGroup[] = [
  {
    label: 'Conversation',
    items: [{ id: 'chat', label: 'Chat', Icon: ChatIcon }],
  },
]

interface Props {
  mobileOpen?: boolean
  onMobileClose?: () => void
}

export function Sidebar({ mobileOpen, onMobileClose }: Props) {
  const activeTab = useSettingsStore((s) => s.activeTab)
  const setActiveTab = useSettingsStore((s) => s.setActiveTab)
  const sidebarOpen = useSettingsStore((s) => s.sidebarOpen)
  const sessions = useChatStore((s) => s.sessions)
  const activeSessionId = useChatStore((s) => s.activeSessionId)
  const selectSession = useChatStore((s) => s.selectSession)
  const newSession = useChatStore((s) => s.newSession)
  const selectedModel = useSettingsStore((s) => s.selectedModels.chat)
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return sessions
    return sessions.filter((c) => c.title.toLowerCase().includes(q))
  }, [sessions, search])

  const handleDelete = (session: Session) => {
    // API deletion not implemented yet
  }

  const exportConversation = (session: Session) => {
    // Export requires fetching messages first
  }

  const expanded = sidebarOpen || mobileOpen

  return (
    <aside
      aria-label="Primary navigation"
      className={cn(
        'flex flex-col h-full bg-[#0d0d11] border-r border-white/[0.05] transition-all duration-200 ease-out',
        'fixed top-0 left-0 z-40 w-72 h-[100dvh] md:static md:h-full md:w-auto',
        mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
        sidebarOpen ? 'md:w-64' : 'md:w-[60px]',
      )}
    >
      <div className={cn('flex items-center gap-2.5 h-14 shrink-0 border-b border-white/[0.04]', expanded ? 'px-4' : 'md:px-3 md:justify-center px-4')}>
        {expanded && <VeniceWordmark className="text-[15px] tracking-tight" />}
        <button
          onClick={onMobileClose}
          aria-label="Close menu"
          className="md:hidden ml-auto p-1 text-white/45 hover:text-white/80 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)]"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
        </button>
      </div>

      <nav aria-label="Sections" className="flex flex-col gap-3 py-3 overflow-y-auto">
        {navGroups.map((group) => (
          <div key={group.label} className={cn(expanded ? 'px-2' : 'md:px-1.5 px-2')}>
            {expanded && (
              <div className="px-2 pb-1.5 text-[10.5px] uppercase tracking-[0.1em] text-white/30 font-semibold">
                {group.label}
              </div>
            )}
            <div className="flex flex-col gap-px">
              {group.items.map(({ id, label, Icon }) => {
                const isActive = activeTab === id
                return (
                  <button
                    key={id}
                    onClick={() => { setActiveTab(id); onMobileClose?.() }}
                    aria-current={isActive ? 'page' : undefined}
                    title={!expanded ? label : undefined}
                    className={cn(
                      'relative flex items-center gap-2.5 rounded-lg text-[14px] transition-all duration-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] focus-visible:outline-offset-2',
                      expanded ? 'px-2.5 py-2' : 'md:px-0 md:py-2 md:justify-center px-2.5 py-2',
                      isActive
                        ? 'bg-white/[0.06] text-white'
                        : 'text-white/55 hover:text-white hover:bg-white/[0.03]',
                    )}
                  >
                    {isActive && (
                      <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 rounded-full bg-[var(--color-accent)]" />
                    )}
                    <Icon />
                    {expanded && <span className="font-medium">{label}</span>}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {expanded && activeTab === 'chat' && (
        <div className="flex flex-col flex-1 min-h-0 mt-1 border-t border-white/[0.04]">
          <div className="flex items-center justify-between px-3 pt-3 pb-1.5">
            <span className="text-[10.5px] font-semibold text-white/40 uppercase tracking-[0.1em]">History</span>
            <button
              onClick={() => newSession(selectedModel || 'llama-3.3-70b')}
              aria-label="New chat"
              className="text-white/55 hover:text-white transition-colors p-1 rounded-md hover:bg-white/[0.05] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)]"
              title="New chat (⌘N)"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
            </button>
          </div>
          {sessions.length > 5 && (
            <div className="px-3 pb-2">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search…"
                aria-label="Search conversations"
                className="w-full bg-white/[0.04] border border-white/[0.06] rounded-md px-2.5 py-1 text-[13px] text-white/85 outline-none focus:border-white/[0.2] placeholder:text-white/30"
              />
            </div>
          )}
          <div className="flex-1 overflow-y-auto px-2 pb-3" role="list">
            {filtered.length === 0 ? (
              <div className="px-2 py-6 text-[13px] text-white/30 text-center">
                {search ? 'No matches' : 'No conversations yet'}
              </div>
            ) : (
              filtered.map((session) => (
                <ConversationRow
                  key={session.id}
                  session={session}
                  isActive={session.id === activeSessionId}
                  onSelect={() => selectSession(session.id)}
                  onDelete={() => handleDelete(session)}
                  onExport={() => exportConversation(session)}
                />
              ))
            )}
          </div>
        </div>
      )}

      {!expanded && <div className="hidden md:block flex-1" />}

      {expanded && (
        <div className="px-3 py-2.5 border-t border-white/[0.04]">
          <div className="text-[11px] text-white/35 space-y-0.5">
            <div className="flex justify-between"><span>New chat</span><kbd className="font-mono text-white/50">⌘N</kbd></div>
          </div>
        </div>
      )}
    </aside>
  )
}

function ConversationRow({ session, isActive, onSelect, onDelete, onExport }: {
  session: Session
  isActive: boolean
  onSelect: () => void
  onDelete: () => void
  onExport: () => void
}) {
  const [confirming, setConfirming] = useState(false)

  return (
    <div
      role="listitem"
      className={cn(
        'group relative flex items-center gap-1 px-2.5 py-1.5 rounded-md text-[13px] cursor-pointer transition-colors',
        isActive
          ? 'bg-white/[0.07] text-white'
          : 'text-white/65 hover:text-white hover:bg-white/[0.03]',
      )}
      onClick={onSelect}
    >
      <span className="truncate flex-1">{session.title || 'Untitled'}</span>
      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity">
        <button
          onClick={(e) => { e.stopPropagation(); onExport() }}
          aria-label={`Export ${session.title}`}
          title="Export as Markdown"
          className="text-white/45 hover:text-white p-1 rounded focus-visible:outline focus-visible:outline-1 focus-visible:outline-[var(--color-accent)]"
        >
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" /></svg>
        </button>
        {confirming ? (
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(); setConfirming(false) }}
            aria-label="Confirm delete"
            className="text-rose-300 hover:text-rose-200 px-1.5 text-[11px] font-semibold rounded"
          >
            Delete?
          </button>
        ) : (
          <button
            onClick={(e) => { e.stopPropagation(); setConfirming(true); setTimeout(() => setConfirming(false), 2500) }}
            aria-label={`Delete ${session.title}`}
            title="Delete"
            className="text-white/45 hover:text-rose-300 p-1 rounded focus-visible:outline focus-visible:outline-1 focus-visible:outline-[var(--color-accent)]"
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </div>
    </div>
  )
}

function conversationToMarkdown(session: Session): string {
  return `# ${session.title}\n\nExport not fully implemented.`
}
