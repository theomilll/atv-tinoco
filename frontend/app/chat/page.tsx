'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { conversations as conversationsApi, Conversation, Message as MessageType, StreamCallbacks } from '@/lib/api'
import { Barcode, Message } from '@/components'


export default function ChatPage() {
  const router = useRouter()
  const { user, loading: authLoading, logout } = useAuth()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<MessageType[]>([])
  const [inputValue, setInputValue] = useState('')
  const [sending, setSending] = useState(false)
  const [loadingConversations, setLoadingConversations] = useState(true)
  const [streamingContent, setStreamingContent] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (user) {
      loadConversations()
    }
  }, [user])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadConversations = async (search?: string) => {
    try {
      const data = await conversationsApi.list(search)
      setConversations(data)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    } finally {
      setLoadingConversations(false)
    }
  }

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      loadConversations(searchQuery || undefined)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const loadConversation = async (id: number) => {
    try {
      const data = await conversationsApi.get(id)
      setCurrentConversation(data)
      setMessages(data.messages || [])
    } catch (error) {
      console.error('Failed to load conversation:', error)
    }
  }

  const handleNewConversation = async () => {
    try {
      const newConv = await conversationsApi.create('NEW SESSION')
      setConversations([newConv, ...conversations])
      setCurrentConversation(newConv)
      setMessages([])
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const handleDeleteConversation = async (id: number) => {
    if (!confirm('TERMINATE THIS SESSION?')) return

    try {
      await conversationsApi.delete(id)
      setConversations(conversations.filter(c => c.id !== id))
      if (currentConversation?.id === id) {
        setCurrentConversation(null)
        setMessages([])
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || !currentConversation || sending) return

    const messageContent = inputValue.trim()
    setInputValue('')
    setSending(true)
    setStreamingContent('')

    try {
      await conversationsApi.sendMessageStream(
        currentConversation.id,
        messageContent,
        {
          onUserMessage: (userMsg) => {
            setMessages(prev => [...prev, userMsg])
          },
          onChunk: (chunk) => {
            setStreamingContent(prev => prev + chunk)
          },
          onAssistantMessage: (assistantMsg) => {
            setStreamingContent('')
            setMessages(prev => {
              const lastMsg = prev[prev.length - 1]
              if (lastMsg?.role === 'user') {
                return [...prev, assistantMsg]
              }
              return prev
            })
          },
          onError: (error) => {
            setStreamingContent('')
            alert(`ERROR: ${error}`)
          },
          onDone: () => {
            loadConversations()
          }
        }
      )
    } catch (error) {
      console.error('Failed to send message:', error)
      alert(`ERROR: ${error instanceof Error ? error.message : 'TRANSMISSION FAILED'}`)
    } finally {
      setSending(false)
      setStreamingContent('')
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
      router.push('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-bg-dark flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg tracking-wider mb-2">INITIALIZING</div>
          <div className="text-xs text-text-muted tracking-widest">PLEASE WAIT...</div>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="h-screen bg-bg-dark flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-bg-surface">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-8">
            <div className="text-xl tracking-wider">CHATGEPETO</div>
            <Barcode width={80} height={24} />
          </div>
          <div className="flex items-center gap-6">
            <button onClick={() => router.push('/documents')} className="btn text-xs py-2 px-4">
              KNOWLEDGE BASE
            </button>
            <div className="text-xs tracking-wide text-text-muted">
              USER: <span className="text-white">{user.username.toUpperCase()}</span>
            </div>
            <button onClick={handleLogout} className="btn text-xs py-2 px-4">
              DISCONNECT
            </button>
          </div>
        </div>

        {/* Status Bar */}
        <div className="px-6 py-2 border-t border-dotted border-border flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <div className="status-dot" />
            <span className="text-text-muted tracking-wide">SYSTEM ONLINE</span>
          </div>
          <div className="text-text-muted">
            {conversations.length} SESSION{conversations.length !== 1 ? 'S' : ''} | {messages.length} MSG{messages.length !== 1 ? 'S' : ''}
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside className="w-72 border-r border-border bg-bg-surface flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-dotted border-border space-y-3">
            <button onClick={handleNewConversation} className="btn btn-primary w-full text-xs">
              + NEW SESSION
            </button>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="SEARCH SESSIONS..."
              className="input w-full text-xs"
            />
          </div>

          {/* Conversation List */}
          <div className="flex-1 overflow-y-auto">
            {loadingConversations ? (
              <div className="p-4 text-center text-text-muted text-xs">
                LOADING...
              </div>
            ) : conversations.length === 0 ? (
              <div className="p-4 text-center text-text-muted text-xs">
                NO ACTIVE SESSIONS
              </div>
            ) : (
              <div className="p-2">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`p-3 mb-1 border cursor-pointer transition-colors group ${
                      currentConversation?.id === conv.id
                        ? 'bg-accent/20 border-accent'
                        : 'border-transparent hover:bg-bg-elevated hover:border-border'
                    }`}
                    onClick={() => loadConversation(conv.id)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm truncate ${
                          currentConversation?.id === conv.id ? 'text-accent-light' : 'text-white'
                        }`}>
                          {currentConversation?.id === conv.id && '> '}
                          {conv.title?.toUpperCase() || 'UNTITLED'}
                        </div>
                        <div className="text-xs text-text-muted mt-1">
                          {conv.message_count} MSG{conv.message_count !== 1 ? 'S' : ''}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteConversation(conv.id)
                        }}
                        className="text-text-muted hover:text-red-400 text-sm leading-none opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Delete"
                      >
                        X
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-dotted border-border">
            <div className="flex items-center justify-between text-xs text-text-muted">
              <span>MSG COUNT</span>
              <span className="text-white">{String(messages.length).padStart(4, '0')}</span>
            </div>
            <div className="mt-3">
              <Barcode width={100} height={30} className="mx-auto" />
            </div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col bg-bg-dark">
          {!currentConversation ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <div className="text-2xl tracking-wider mb-2">NO SESSION SELECTED</div>
              <div className="text-sm text-text-muted max-w-md">
                CREATE A NEW SESSION OR SELECT AN EXISTING ONE FROM THE SIDEBAR TO BEGIN.
              </div>
            </div>
          ) : (
            <>
              {/* Session Header */}
              <div className="px-6 py-3 border-b border-border bg-bg-surface flex items-center justify-between">
                <div>
                  <div className="text-xs text-text-muted tracking-wider">ACTIVE SESSION</div>
                  <div className="text-lg tracking-wide mt-1">
                    {currentConversation.title?.toUpperCase() || 'UNTITLED'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-text-muted">SESSION ID</div>
                  <div className="text-sm text-white">#{String(currentConversation.id).padStart(6, '0')}</div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6">
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center">
                    <div className="text-lg tracking-wider mb-2">READY FOR INPUT<span className="blink">_</span></div>
                    <div className="text-sm text-text-muted">
                      TYPE YOUR MESSAGE BELOW TO BEGIN.
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4 max-w-4xl mx-auto">
                    {messages.map((msg) => (
                      <Message
                        key={msg.id}
                        role={msg.role}
                        content={msg.content}
                        username={user.username}
                        citations={msg.citations}
                        attachments={msg.attachments}
                      />
                    ))}
                    {streamingContent && (
                      <Message
                        role="assistant"
                        content={streamingContent}
                        username={user.username}
                      />
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div className="border-t border-border bg-bg-surface p-4">
                <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto">
                  <div className="flex gap-4 items-end">
                    <div className="flex-1">
                      <label className="text-xs text-text-muted tracking-wider block mb-2">MESSAGE</label>
                      <textarea
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="ENTER MESSAGE..."
                        className="input resize-none"
                        disabled={sending}
                        rows={2}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault()
                            handleSendMessage(e)
                          }
                        }}
                      />
                    </div>
                    <div className="flex flex-col items-center gap-2">
                      <Barcode width={40} height={50} />
                      <button
                        type="submit"
                        disabled={sending || !inputValue.trim()}
                        className="btn btn-primary text-xs whitespace-nowrap"
                      >
                        {sending ? 'SENDING...' : 'TRANSMIT'}
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  )
}
