'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { documents as documentsApi, Document } from '@/lib/api'
import { Barcode } from '@/components'

const ACCEPTED_DOC_TYPES = '.pdf,.txt,.docx'

export default function DocumentsPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [docs, setDocs] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [urlModalOpen, setUrlModalOpen] = useState(false)
  const [urlInput, setUrlInput] = useState('')
  const [titleInput, setTitleInput] = useState('')
  const [urlLoading, setUrlLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (user) {
      loadDocuments()
    }
  }, [user])

  const loadDocuments = async () => {
    try {
      const data = await documentsApi.list()
      setDocs(data)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    try {
      for (const file of Array.from(files)) {
        await documentsApi.upload(file)
      }
      await loadDocuments()
    } catch (error) {
      console.error('Upload failed:', error)
      alert(`UPLOAD ERROR: ${error instanceof Error ? error.message : 'FAILED'}`)
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleUrlIngest = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!urlInput.trim()) return

    setUrlLoading(true)
    try {
      await documentsApi.fromUrl(urlInput, titleInput || undefined)
      await loadDocuments()
      setUrlModalOpen(false)
      setUrlInput('')
      setTitleInput('')
    } catch (error) {
      console.error('URL ingestion failed:', error)
      alert(`INGEST ERROR: ${error instanceof Error ? error.message : 'FAILED'}`)
    } finally {
      setUrlLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('DELETE THIS DOCUMENT?')) return

    try {
      await documentsApi.delete(id)
      setDocs(docs.filter(d => d.id !== id))
    } catch (error) {
      console.error('Delete failed:', error)
    }
  }

  const handleReprocess = async (id: number) => {
    try {
      await documentsApi.reprocess(id)
      await loadDocuments()
    } catch (error) {
      console.error('Reprocess failed:', error)
      alert(`REPROCESS ERROR: ${error instanceof Error ? error.message : 'FAILED'}`)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400'
      case 'processing': return 'text-yellow-400'
      case 'failed': return 'text-red-400'
      default: return 'text-text-muted'
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
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

  if (!user) return null

  return (
    <div className="min-h-screen bg-bg-dark">
      {/* Header */}
      <header className="border-b border-border bg-bg-surface">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-8">
            <div className="text-xl tracking-wider">KNOWLEDGE BASE</div>
            <Barcode width={80} height={24} />
          </div>
          <div className="flex items-center gap-4">
            <button onClick={() => router.push('/chat')} className="btn text-xs py-2 px-4">
              BACK TO CHAT
            </button>
          </div>
        </div>

        {/* Status Bar */}
        <div className="px-6 py-2 border-t border-dotted border-border flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <div className="status-dot" />
            <span className="text-text-muted tracking-wide">DOCUMENT STORAGE ONLINE</span>
          </div>
          <div className="text-text-muted">
            {docs.length} DOCUMENT{docs.length !== 1 ? 'S' : ''} | {docs.filter(d => d.status === 'completed').reduce((acc, d) => acc + d.chunk_count, 0)} CHUNKS
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="max-w-6xl mx-auto">
          {/* Actions */}
          <div className="flex gap-4 mb-6">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={ACCEPTED_DOC_TYPES}
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="btn btn-primary text-xs"
            >
              {uploading ? 'UPLOADING...' : '+ UPLOAD FILE'}
            </button>
            <button
              onClick={() => setUrlModalOpen(true)}
              className="btn text-xs"
            >
              + ADD URL
            </button>
          </div>

          {/* Document List */}
          {loading ? (
            <div className="text-center py-12 text-text-muted">LOADING DOCUMENTS...</div>
          ) : docs.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-border">
              <div className="text-lg tracking-wider mb-2">NO DOCUMENTS</div>
              <div className="text-sm text-text-muted">UPLOAD A FILE OR ADD A URL TO BUILD YOUR KNOWLEDGE BASE</div>
            </div>
          ) : (
            <div className="grid gap-4">
              {docs.map((doc) => (
                <div
                  key={doc.id}
                  className="bg-bg-surface border border-border p-4 hover:border-accent transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-lg">
                          {doc.file_type === 'application/pdf' ? '📄' :
                           doc.file_type === 'text/html' ? '🌐' :
                           doc.file_type === 'text/plain' ? '📝' : '📁'}
                        </span>
                        <h3 className="text-white truncate">{doc.title.toUpperCase()}</h3>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-text-muted">
                        <span className={getStatusColor(doc.status)}>{doc.status.toUpperCase()}</span>
                        <span>{formatFileSize(doc.file_size)}</span>
                        <span>{doc.chunk_count} CHUNKS</span>
                        <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {doc.status === 'failed' && (
                        <button
                          onClick={() => handleReprocess(doc.id)}
                          className="btn text-xs py-1 px-3"
                        >
                          RETRY
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="text-text-muted hover:text-red-400 text-sm"
                        title="Delete"
                      >
                        X
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* URL Modal */}
      {urlModalOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-bg-surface border border-border p-6 w-full max-w-md">
            <h2 className="text-lg tracking-wider mb-4">ADD URL</h2>
            <form onSubmit={handleUrlIngest}>
              <div className="mb-4">
                <label className="text-xs text-text-muted tracking-wider block mb-2">URL</label>
                <input
                  type="url"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://example.com/article"
                  className="input w-full"
                  required
                />
              </div>
              <div className="mb-6">
                <label className="text-xs text-text-muted tracking-wider block mb-2">TITLE (OPTIONAL)</label>
                <input
                  type="text"
                  value={titleInput}
                  onChange={(e) => setTitleInput(e.target.value)}
                  placeholder="Custom title"
                  className="input w-full"
                />
              </div>
              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => {
                    setUrlModalOpen(false)
                    setUrlInput('')
                    setTitleInput('')
                  }}
                  className="btn text-xs flex-1"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={urlLoading || !urlInput.trim()}
                  className="btn btn-primary text-xs flex-1"
                >
                  {urlLoading ? 'LOADING...' : 'INGEST'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
